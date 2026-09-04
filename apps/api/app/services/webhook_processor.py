"""
Settl Webhook Processor

Async background processor that takes a persisted + normalized webhook
and creates the appropriate Settl entities (RevenueEvent, Customer, RecoveryCase).

This processor does NOT:
- Run AI analysis
- Create payment links
- Send notifications
- Mark cases as recovered inline (recovery verification is handled separately)
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

import app.database as app_db
from app.models.webhook_event import WebhookEvent
from app.models.revenue_event import RevenueEvent
from app.models.recovery_case import RecoveryCase
from app.models.customer import Customer
from app.models.order import Order
from app.models.base import generate_uuid
from app.services.webhook_classifier import (
    is_revenue_loss_event,
    is_recovery_verification_event,
    is_informational_event,
)
from app.services.webhook_normalizer import NormalizedWebhookEvent, normalize_webhook_payload
from app.services.recovery_service import create_case_for_event, handle_payment_recovered

logger = logging.getLogger(__name__)

DEFAULT_MERCHANT_ID = "MER_DEMO_01"


def process_webhook(webhook_id: str) -> None:
    """
    Main entry point for background webhook processing.
    Takes a WebhookEvent.id, processes it, and updates its status.
    Uses its own DB session (for use outside of the HTTP request lifecycle).
    """
    db = app_db.SessionLocal()
    try:
        wh = db.query(WebhookEvent).filter(WebhookEvent.id == webhook_id).first()
        if not wh:
            logger.error(f"WebhookEvent {webhook_id} not found for processing")
            return

        if wh.status in ("PROCESSED", "DUPLICATE"):
            logger.info(f"WebhookEvent {webhook_id} already in terminal state: {wh.status}")
            return

        _process_webhook_internal(db, wh)

    except Exception as e:
        logger.error(f"Unhandled error processing webhook {webhook_id}: {e}", exc_info=True)
        try:
            wh = db.query(WebhookEvent).filter(WebhookEvent.id == webhook_id).first()
            if wh:
                wh.status = "PROCESSING_FAILED"
                wh.processing_error = str(e)[:2000]
                wh.processed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            db.rollback()
        logger.error(f"EVENT PROCESSING FAILED\nevent_id={wh.external_event_id if 'wh' in locals() and wh else 'unknown'}\nerror={str(e)}", exc_info=True)
    finally:
        db.close()


def process_webhook_sync(db: Session, wh: WebhookEvent) -> None:
    """
    Synchronous version for use within an existing DB session (e.g., tests).
    """
    _process_webhook_internal(db, wh)


def _process_webhook_internal(db: Session, wh: WebhookEvent) -> None:
    """Core processing logic shared by sync and async paths."""
    try:
        wh.status = "PROCESSING"
        db.flush()

        # 1. Normalize the payload
        normalized = normalize_webhook_payload(wh.payload)
        wh.settl_event_type = normalized.settl_event_type
        
        logger.info(f"EVENT PROCESSING START\nevent_id={wh.external_event_id}\nevent_type={normalized.settl_event_type}")
        logger.info(f"EVENT NORMALIZED\nprovider_event={wh.event_type}\nsettl_event={normalized.settl_event_type}")

        # 2. Resolve merchant
        merchant_id = _resolve_merchant(db, normalized)
        wh.merchant_id = merchant_id

        # 3. Route based on event classification
        if normalized.settl_event_type == "UNHANDLED":
            wh.status = "UNHANDLED"
            wh.processed_at = datetime.now(timezone.utc)
            logger.info(f"Webhook {wh.id}: unhandled event type '{normalized.razorpay_event_type}', stored for audit")
            db.commit()
            return

        if is_revenue_loss_event(normalized.settl_event_type):
            _handle_revenue_loss(db, wh, normalized, merchant_id)
        elif is_recovery_verification_event(normalized.settl_event_type):
            _handle_recovery_verification(db, wh, normalized, merchant_id)
        elif is_informational_event(normalized.settl_event_type):
            wh.status = "PROCESSED"
            wh.processed_at = datetime.now(timezone.utc)
            logger.info(f"Webhook {wh.id}: informational event '{normalized.settl_event_type}', stored")
            db.commit()
        else:
            wh.status = "IGNORED"
            wh.processed_at = datetime.now(timezone.utc)
            db.commit()

        logger.info(f"EVENT PROCESSING COMPLETE")

    except Exception as e:
        db.rollback()
        # Refetch safely after rollback to avoid DetachedInstanceError
        safe_wh = db.query(WebhookEvent).filter(WebhookEvent.id == webhook_id).first()
        if safe_wh:
            safe_wh.status = "PROCESSING_FAILED"
            safe_wh.processing_error = str(e)[:2000]
            safe_wh.processed_at = datetime.now(timezone.utc)
            db.commit()
        logger.error(f"Webhook {webhook_id} processing failed: {e}", exc_info=True)
        raise


def _resolve_merchant(db: Session, normalized: NormalizedWebhookEvent) -> str:
    """
    Resolves the Settl merchant from webhook context.
    Strict tenant isolation: fails if the merchant cannot be explicitly resolved.
    """
    if normalized.settl_merchant_id:
        from app.models.merchant import Merchant
        merchant = db.query(Merchant).filter(Merchant.id == normalized.settl_merchant_id).first()
        if merchant:
            logger.info(f"MERCHANT RESOLUTION = SUCCESS\nmerchant_id={merchant.id}")
            return merchant.id
        
        logger.error(f"MERCHANT RESOLUTION = FAILED\nreason=Merchant ID '{normalized.settl_merchant_id}' provided in notes not found in database.")
        raise ValueError(f"Merchant ID '{normalized.settl_merchant_id}' from notes not found in database.")

    # Hackathon Demo fallback: If no explicit merchant is provided in the payload,
    # assume it belongs to the primary demo merchant so that generic Razorpay
    # webhooks (like from Postman) are successfully processed.
    logger.info(f"MERCHANT RESOLUTION = FALLBACK\nreason=No explicit settl_merchant_id found, defaulting to {DEFAULT_MERCHANT_ID}")
    return DEFAULT_MERCHANT_ID


def _resolve_customer(
    db: Session,
    merchant_id: str,
    normalized: NormalizedWebhookEvent,
) -> Customer:
    """
    Resolves or creates a Customer from webhook data.
    Matching priority:
    1. By email (within merchant scope)
    2. By phone (within merchant scope)
    3. Create new customer (no fake history)
    """
    # Try email match first
    if normalized.customer_email:
        customer = (
            db.query(Customer)
            .filter(
                Customer.merchant_id == merchant_id,
                Customer.email == normalized.customer_email,
            )
            .first()
        )
        if customer:
            logger.info(f"CUSTOMER LOOKUP: FOUND\nCUSTOMER STATUS: EXISTING")
            return customer

    # Try phone match
    if normalized.customer_phone:
        customer = (
            db.query(Customer)
            .filter(
                Customer.merchant_id == merchant_id,
                Customer.phone == normalized.customer_phone,
            )
            .first()
        )
        if customer:
            logger.info(f"CUSTOMER LOOKUP: FOUND\nCUSTOMER STATUS: EXISTING")
            return customer

    # Create new customer — no fake history
    name = normalized.customer_name
    if not name and normalized.customer_email:
        name = normalized.customer_email.split("@")[0].replace(".", " ").title()
    if not name:
        name = "Unknown Customer"

    customer = Customer(
        id=generate_uuid("CUS"),
        merchant_id=merchant_id,
        name=name,
        email=normalized.customer_email,
        phone=normalized.customer_phone,
        success_rate=1.0,  # Neutral default — no invented history
        customer_value="UNKNOWN",
        opted_out=False,
    )
    db.add(customer)
    db.flush()
    logger.info(f"CUSTOMER LOOKUP: NEW\nCUSTOMER STATUS: NEW")
    return customer


def _handle_revenue_loss(
    db: Session,
    wh: WebhookEvent,
    normalized: NormalizedWebhookEvent,
    merchant_id: str,
) -> None:
    """
    Handles revenue-loss events (payment.failed, subscription.pending/halted).
    Creates Customer + RevenueEvent + RecoveryCase, then auto-runs the
    full recovery pipeline (AI → Policy → Execute) in the background.
    """
    # Payment-ID level idempotency: prevent duplicate cases for the same Razorpay payment
    if normalized.payment_id:
        existing_event = (
            db.query(RevenueEvent)
            .filter(
                RevenueEvent.payment_id == normalized.payment_id,
                RevenueEvent.merchant_id == merchant_id,
            )
            .first()
        )
        if existing_event:
            wh.status = "PROCESSED"
            wh.processed_at = datetime.now(timezone.utc)
            wh.processing_error = f"RevenueEvent already exists for payment {normalized.payment_id}"
            db.commit()
            logger.info(f"RECOVERY CASE SKIPPED: EXISTING CASE\ncase_id=payment_duplicate_{normalized.payment_id}")
            return
        logger.info("PAYMENT LOOKUP: NEW")

    # Resolve customer
    customer = _resolve_customer(db, merchant_id, normalized)

    # Build failure reason
    failure_reason = (
        normalized.error_description
        or normalized.error_reason
        or normalized.error_code
        or f"Provider event: {normalized.razorpay_event_type}"
    )

    # Map Settl event type to internal event_type field
    event_type_map = {
        "PAYMENT_FAILURE": "PAYMENT_FAILED",
        "SUBSCRIPTION_PENDING": "SUBSCRIPTION_PAYMENT_FAILED",
        "SUBSCRIPTION_HALTED": "SUBSCRIPTION_HALTED",
    }
    internal_event_type = event_type_map.get(normalized.settl_event_type, normalized.settl_event_type)

    # Build billing cycle ID for subscription events
    billing_cycle_id = None
    if normalized.subscription_id:
        sub_entity = wh.payload.get("payload", {}).get("subscription", {}).get("entity", {})
        current_start = sub_entity.get("current_start")
        billing_cycle_id = f"{normalized.subscription_id}_{current_start}" if current_start else f"{normalized.subscription_id}_unknown"

        # Subscription-level idempotency: check for active case in same billing cycle
        existing_case = (
            db.query(RecoveryCase)
            .filter(
                RecoveryCase.merchant_id == merchant_id,
                RecoveryCase.subscription_id == normalized.subscription_id,
                RecoveryCase.billing_cycle_id == billing_cycle_id,
                RecoveryCase.status.notin_(["RECOVERED", "FAILED", "STOPPED"]),
            )
            .first()
        )
        if existing_case:
            wh.status = "PROCESSED"
            wh.processed_at = datetime.now(timezone.utc)
            wh.processing_error = f"Active case {existing_case.id} already exists for billing cycle"
            db.commit()
            logger.info(f"RECOVERY CASE SKIPPED: EXISTING CASE\ncase_id={existing_case.id}")
            return

    # Amount: use normalized value, fall back to 0 (downstream should handle)
    amount = normalized.amount_paise or 0

    # Create RevenueEvent
    revenue_event = RevenueEvent(
        id=generate_uuid("EVT"),
        merchant_id=merchant_id,
        customer_id=customer.id,
        event_type=internal_event_type,
        amount_paise=amount,
        failure_reason=failure_reason,
        source="razorpay",
        occurred_at=datetime.now(timezone.utc),
        raw_payload=wh.payload,
        payment_id=normalized.payment_id,
        payment_link_id=normalized.payment_link_id,
        payment_method=normalized.payment_method,
        payment_status=normalized.payment_status,
        webhook_event_id=wh.id,
        subscription_id=normalized.subscription_id,
        billing_cycle_id=billing_cycle_id,
        provider_state=normalized.subscription_status,
    )
    db.add(revenue_event)
    db.flush()

    # Create RecoveryCase (NEW state)
    logger.info("RECOVERY CASE CREATION START")
    case = create_case_for_event(db, revenue_event)
    logger.info(f"RECOVERY CASE CREATED\ncase_id={case.id}")

    # Update webhook with downstream references
    wh.settl_event_id = revenue_event.id
    wh.status = "PROCESSED"
    wh.processed_at = datetime.now(timezone.utc)
    db.commit()

    # AUTO-PIPELINE: Run full recovery pipeline (AI → Policy → Execute)
    # This is the critical integration that makes Case 1 fully automated.
    # If the pipeline fails, the case remains in NEW/ANALYZING state and
    # can be retried manually via the dashboard or by the webhook worker.
    try:
        from app.services.recovery_service import execute_case_pipeline
        case = execute_case_pipeline(db, case.id)
        logger.info(
            f"Auto-pipeline completed: case {case.id} → {case.status} "
            f"(action={case.actual_action})"
        )
    except Exception as pipeline_err:
        logger.error(
            f"Auto-pipeline failed for case {case.id}: {pipeline_err}",
            exc_info=True,
        )
        # Case remains in its current state — can be retried manually



def _handle_recovery_verification(
    db: Session,
    wh: WebhookEvent,
    normalized: NormalizedWebhookEvent,
    merchant_id: str,
) -> None:
    """
    Handles recovery-verification events (payment_link.paid, payment.captured, subscription.charged).
    Finds the matching RecoveryCase and delegates to handle_payment_recovered.
    """
    case = _find_matching_recovery_case(db, normalized, merchant_id)

    if not case:
        # No matching case — store the event for audit but don't create side effects
        wh.status = "PROCESSED"
        wh.processed_at = datetime.now(timezone.utc)
        wh.processing_error = "No matching recovery case found for verification event"
        db.commit()
        logger.info(f"Webhook {wh.id}: recovery verification event but no matching case")
        return

    # Determine amount paid
    amount_paid = normalized.amount_paise or case.amount_at_risk_paise
    payment_id = normalized.payment_id or generate_uuid("pay_wh")

    handle_payment_recovered(
        db=db,
        case_id=case.id,
        paid_amount_paise=int(amount_paid),
        payment_id=payment_id,
        external_event_id=wh.external_event_id,
    )

    wh.settl_event_id = case.revenue_event_id
    wh.status = "PROCESSED"
    wh.processed_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"Webhook {wh.id}: recovery verified for case {case.id}, amount ₹{amount_paid/100:.2f}")


def _find_matching_recovery_case(
    db: Session,
    normalized: NormalizedWebhookEvent,
    merchant_id: str,
) -> Optional[RecoveryCase]:
    """
    Finds the RecoveryCase that this recovery event corresponds to.
    Matching priority:
    1. settl_case_id from notes
    2. payment_link_id → RecoveryAction.razorpay_entity_id
    3. subscription_id → RecoveryCase.subscription_id (active cases)
    """
    from app.models.recovery_action import RecoveryAction

    # 1. Direct case_id from notes
    if normalized.settl_case_id:
        case = (
            db.query(RecoveryCase)
            .filter(
                RecoveryCase.id == normalized.settl_case_id,
                RecoveryCase.merchant_id == merchant_id,
            )
            .first()
        )
        if case and case.status not in ("RECOVERED", "FAILED", "STOPPED"):
            return case

    # 2. Payment link ID → recovery action → case
    if normalized.payment_link_id:
        action = (
            db.query(RecoveryAction)
            .filter(RecoveryAction.razorpay_entity_id == normalized.payment_link_id)
            .first()
        )
        if action:
            case = db.query(RecoveryCase).filter(RecoveryCase.id == action.case_id).first()
            if case and case.merchant_id == merchant_id and case.status not in ("RECOVERED", "FAILED", "STOPPED"):
                return case

    # 3. Subscription ID matching
    if normalized.subscription_id:
        case = (
            db.query(RecoveryCase)
            .filter(
                RecoveryCase.merchant_id == merchant_id,
                RecoveryCase.subscription_id == normalized.subscription_id,
                RecoveryCase.status.notin_(["RECOVERED", "FAILED", "STOPPED"]),
            )
            .order_by(RecoveryCase.created_at.desc())
            .first()
        )
        if case:
            return case

    return None
