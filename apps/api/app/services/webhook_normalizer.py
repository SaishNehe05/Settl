"""
Settl Webhook Normalizer

Extracts structured data from raw Razorpay webhook payloads into a
provider-agnostic NormalizedWebhookEvent dataclass.
Does NOT invent values for fields that Razorpay did not provide.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.services.webhook_classifier import classify_event, get_event_family

logger = logging.getLogger(__name__)


@dataclass
class NormalizedWebhookEvent:
    """Provider-agnostic normalized event produced from a Razorpay webhook."""
    provider: str = "razorpay"
    razorpay_event_type: str = ""          # Original: "payment.failed"
    settl_event_type: str = ""             # Normalized: "PAYMENT_FAILURE"
    account_id: Optional[str] = None       # Razorpay account_id from payload

    # Payment context
    payment_id: Optional[str] = None
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    amount_paise: Optional[int] = None
    currency: str = "INR"

    # Customer context
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None

    # Order / link context
    order_id: Optional[str] = None
    payment_link_id: Optional[str] = None

    # Subscription context
    subscription_id: Optional[str] = None
    subscription_status: Optional[str] = None

    # Failure context
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_reason: Optional[str] = None

    # Settl references extracted from notes
    settl_case_id: Optional[str] = None
    settl_merchant_id: Optional[str] = None


def normalize_webhook_payload(payload: Dict[str, Any]) -> NormalizedWebhookEvent:
    """
    Entry point: classifies the event family and delegates to the appropriate
    normalizer. Returns a NormalizedWebhookEvent with all available fields
    extracted; fields not present in the payload remain None.
    """
    razorpay_event_type = payload.get("event", "unknown")
    settl_event_type = classify_event(razorpay_event_type)
    account_id = payload.get("account_id")
    family = get_event_family(razorpay_event_type)

    base = NormalizedWebhookEvent(
        razorpay_event_type=razorpay_event_type,
        settl_event_type=settl_event_type,
        account_id=account_id,
    )

    try:
        if family == "payment":
            _normalize_payment(base, payload)
        elif family == "payment_link":
            _normalize_payment_link(base, payload)
        elif family == "subscription":
            _normalize_subscription(base, payload)
        elif family == "order":
            _normalize_order(base, payload)
        else:
            logger.info(f"No specific normalizer for event family '{family}', using base fields only")
    except Exception as e:
        logger.error(f"Normalization error for {razorpay_event_type}: {e}", exc_info=True)
        # Return partially-normalized event rather than crashing
        base.error_description = f"Normalization error: {str(e)}"

    return base


# ─── Family-specific normalizers ────────────────────────────────────


def _normalize_payment(event: NormalizedWebhookEvent, payload: Dict[str, Any]) -> None:
    """Normalize payment.failed / payment.authorized / payment.captured events."""
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    if not entity:
        return

    event.payment_id = entity.get("id")
    event.payment_status = entity.get("status")
    event.payment_method = entity.get("method")
    event.amount_paise = entity.get("amount")
    event.currency = entity.get("currency", "INR")
    event.order_id = entity.get("order_id")

    # Customer info from payment entity
    event.customer_email = entity.get("email") or None
    event.customer_phone = entity.get("contact") or None
    # Razorpay payment entities do not usually carry customer name directly
    # but notes might
    notes = entity.get("notes", {})
    event.customer_name = notes.get("customer_name") or None

    # Failure context
    event.error_code = entity.get("error_code") or None
    event.error_description = entity.get("error_description") or None
    event.error_reason = entity.get("error_reason") or None

    # Subscription linkage (for subscription-triggered payment events)
    event.subscription_id = entity.get("subscription_id") or None

    # Settl references from notes
    if isinstance(notes, dict):
        event.settl_case_id = notes.get("case_id") or notes.get("settl_case_id") or None
        event.settl_merchant_id = notes.get("merchant_id") or notes.get("settl_merchant_id") or None


def _normalize_payment_link(event: NormalizedWebhookEvent, payload: Dict[str, Any]) -> None:
    """Normalize payment_link.paid / partially_paid / cancelled / expired events."""
    plink_entity = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

    if plink_entity:
        event.payment_link_id = plink_entity.get("id")
        event.amount_paise = plink_entity.get("amount_paid") or plink_entity.get("amount")
        event.currency = plink_entity.get("currency", "INR")

        # Customer from payment link
        customer = plink_entity.get("customer", {})
        if customer:
            event.customer_name = customer.get("name") or None
            event.customer_email = customer.get("email") or None
            event.customer_phone = customer.get("contact") or None

        # Settl references from notes
        notes = plink_entity.get("notes", {})
        if isinstance(notes, dict):
            event.settl_case_id = notes.get("case_id") or notes.get("settl_case_id") or None
            event.settl_merchant_id = notes.get("merchant_id") or notes.get("settl_merchant_id") or None

        # Extract reference_id for case matching fallback
        ref_id = plink_entity.get("reference_id", "")
        if ref_id and ref_id.startswith("settl_") and not event.settl_case_id:
            # Format: settl_{case_id}_{attempt}
            parts = ref_id.split("_", 2)
            if len(parts) >= 2:
                # Reconstruct potential case_id (e.g., "CASE_xxxx")
                event.settl_case_id = parts[1] if len(parts) == 2 else f"{parts[1]}"

    if payment_entity:
        event.payment_id = payment_entity.get("id")
        event.payment_status = payment_entity.get("status")
        event.payment_method = payment_entity.get("method")
        event.order_id = payment_entity.get("order_id")


def _normalize_subscription(event: NormalizedWebhookEvent, payload: Dict[str, Any]) -> None:
    """Normalize subscription.pending / halted / charged / activated / etc."""
    sub_entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

    if sub_entity:
        event.subscription_id = sub_entity.get("id")
        event.subscription_status = sub_entity.get("status")

        # Amount: not always present in subscription entity; try notes or plan
        notes = sub_entity.get("notes", {})
        if isinstance(notes, dict):
            amt = notes.get("expected_amount_paise")
            if amt is not None:
                event.amount_paise = int(amt)
            event.customer_email = notes.get("customer_email") or None
            event.customer_phone = notes.get("customer_phone") or None
            event.settl_case_id = notes.get("case_id") or notes.get("settl_case_id") or None
            event.settl_merchant_id = notes.get("merchant_id") or notes.get("settl_merchant_id") or None

        # Billing cycle identification
        current_start = sub_entity.get("current_start")
        if current_start and event.subscription_id:
            # Store as a composite key for cycle-level idempotency
            pass  # billing_cycle_id is set in the processor, not the normalizer

    if payment_entity:
        event.payment_id = payment_entity.get("id")
        event.payment_status = payment_entity.get("status")
        event.payment_method = payment_entity.get("method")
        event.amount_paise = event.amount_paise or payment_entity.get("amount")
        event.order_id = payment_entity.get("order_id")
        event.customer_email = event.customer_email or payment_entity.get("email") or None
        event.customer_phone = event.customer_phone or payment_entity.get("contact") or None

        # Check for subscription_id in payment entity (for subscription.charged via payment webhook)
        if not event.subscription_id:
            event.subscription_id = payment_entity.get("subscription_id") or None


def _normalize_order(event: NormalizedWebhookEvent, payload: Dict[str, Any]) -> None:
    """Normalize order.paid events."""
    order_entity = payload.get("payload", {}).get("order", {}).get("entity", {})
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

    if order_entity:
        event.order_id = order_entity.get("id")
        event.amount_paise = order_entity.get("amount_paid") or order_entity.get("amount")
        event.currency = order_entity.get("currency", "INR")

        notes = order_entity.get("notes", {})
        if isinstance(notes, dict):
            event.settl_case_id = notes.get("case_id") or None
            event.settl_merchant_id = notes.get("merchant_id") or None

    if payment_entity:
        event.payment_id = payment_entity.get("id")
        event.payment_status = payment_entity.get("status")
        event.payment_method = payment_entity.get("method")
