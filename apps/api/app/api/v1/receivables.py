from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from app.database import get_db
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.revenue_event import RevenueEvent
from app.models.recovery_case import RecoveryCase
from app.api.deps import get_current_merchant
from app.schemas.receivables import (
    ReceivableEventCreate,
    ReceivableEventResponse,
    ReceivablesStatusResponse,
)
from app.schemas.event import EventCreate
from app.services.event_service import ingest_revenue_event
from app.services.recovery_service import handle_payment_recovered
from app.services.audit_service import log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/receivables", tags=["B2B Receivables"])


@router.get("/status", response_model=ReceivablesStatusResponse)
def get_receivables_status(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    """
    Returns the merchant's B2B receivables integration status.
    If no real receivables events have been ingested, returns connected=False.
    """
    invoices = db.query(Invoice).filter(Invoice.merchant_id == current_merchant.id).all()
    invoice_count = len(invoices)
    
    if invoice_count == 0:
        return ReceivablesStatusResponse(
            connected=False,
            status_text="Receivables integration not connected",
            invoice_count=0,
            overdue_count=0,
            paid_count=0,
            last_event_at=None,
        )

    overdue_count = sum(1 for inv in invoices if inv.status in ("OVERDUE", "PARTIALLY_PAID") and inv.paid_amount_paise < inv.amount_paise)
    paid_count = sum(1 for inv in invoices if inv.status == "PAID" or inv.paid_amount_paise >= inv.amount_paise)

    # Find timestamp of most recent invoice
    latest_inv = max(invoices, key=lambda x: x.created_at or datetime.min.replace(tzinfo=timezone.utc))

    return ReceivablesStatusResponse(
        connected=True,
        status_text="Receivables integration active",
        invoice_count=invoice_count,
        overdue_count=overdue_count,
        paid_count=paid_count,
        last_event_at=latest_inv.created_at,
    )


@router.post("/events", response_model=ReceivableEventResponse, status_code=status.HTTP_200_OK)
def ingest_receivable_event(
    data: ReceivableEventCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    """
    Ingests a real B2B receivable event from a merchant billing or ERP system.
    Strict tenant isolation: the event is bound to current_merchant.
    """
    now = datetime.now(timezone.utc)

    # 1. Merchant authorization & tenant validation
    if data.merchant_id and data.merchant_id != current_merchant.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant mismatch: authenticated as {current_merchant.id}, cannot ingest events for {data.merchant_id}",
        )

    # 2. Idempotency Check: Prevent duplicate event processing
    existing_event = (
        db.query(RevenueEvent)
        .filter(
            RevenueEvent.merchant_id == current_merchant.id,
            RevenueEvent.raw_payload["event_id"].astext == data.event_id
        )
        .first()
    ) if hasattr(RevenueEvent, 'raw_payload') else None

    # Secondary check in audit logs or external IDs
    if not existing_event:
        existing_rev = (
            db.query(RevenueEvent)
            .filter(
                RevenueEvent.merchant_id == current_merchant.id,
                RevenueEvent.source == "merchant_erp"
            )
            .all()
        )
        for rev in existing_rev:
            if rev.raw_payload and rev.raw_payload.get("event_id") == data.event_id:
                existing_event = rev
                break

    if existing_event:
        logger.info(f"Duplicate receivable event {data.event_id} ignored for merchant {current_merchant.id}")
        linked_case = existing_event.recovery_case
        return ReceivableEventResponse(
            status="duplicate_ignored",
            event_id=data.event_id,
            invoice_id=data.invoice_id,
            internal_invoice_id=existing_event.invoice_id or "",
            event_type=data.status,
            action_taken="DUPLICATE_EVENT_IGNORED",
            case_id=linked_case.id if linked_case else None,
            processed_at=now,
        )

    # 3. Resolve or create customer within merchant tenant scope
    customer = None
    if data.customer_email:
        customer = (
            db.query(Customer)
            .filter(Customer.merchant_id == current_merchant.id, Customer.email == data.customer_email)
            .first()
        )
    if not customer and data.customer_phone:
        customer = (
            db.query(Customer)
            .filter(Customer.merchant_id == current_merchant.id, Customer.phone == data.customer_phone)
            .first()
        )
    if not customer:
        cust_name = data.customer_name or f"B2B Customer ({data.customer_id or data.invoice_id})"
        customer = Customer(
            merchant_id=current_merchant.id,
            name=cust_name,
            email=data.customer_email,
            phone=data.customer_phone,
            success_rate=1.0,
            customer_value="ENTERPRISE" if data.amount_paise >= 10000000 else "B2B_STANDARD",
            opted_out=False,
        )
        db.add(customer)
        db.flush()

    # 4. Resolve or create Invoice
    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.merchant_id == current_merchant.id,
            Invoice.external_invoice_id == data.invoice_id
        )
        .first()
    )

    due_date = data.due_at
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)

    if not invoice:
        invoice = Invoice(
            merchant_id=current_merchant.id,
            customer_id=customer.id,
            external_invoice_id=data.invoice_id,
            amount_paise=data.amount_paise,
            paid_amount_paise=data.paid_amount_paise or 0,
            currency=data.currency,
            due_at=due_date,
            status="ISSUED" if data.status in ("INVOICE_CREATED", "ISSUED") else data.status,
        )
        db.add(invoice)
        db.flush()
    else:
        # Update existing invoice data
        invoice.amount_paise = data.amount_paise
        if data.paid_amount_paise is not None:
            invoice.paid_amount_paise = data.paid_amount_paise
        invoice.due_at = due_date

    event_type = data.status.upper()
    action_taken = "NONE"
    created_case_id = None

    # 5. Process Lifecycle Event
    if event_type in ("INVOICE_CREATED", "ISSUED"):
        invoice.status = "ISSUED"
        action_taken = "INVOICE_PERSISTED"

    elif event_type in ("INVOICE_DUE", "DUE"):
        invoice.status = "DUE"
        action_taken = "INVOICE_MARKED_DUE"

    elif event_type in ("INVOICE_OVERDUE", "OVERDUE"):
        # Section 8 Rule: If actual payment already received, DO NOT create overdue case
        if invoice.paid_amount_paise >= invoice.amount_paise or invoice.status == "PAID":
            invoice.status = "PAID"
            action_taken = "ALREADY_PAID_OVERDUE_SKIPPED"
        else:
            invoice.status = "OVERDUE"
            
            # Idempotency check: Does an active RecoveryCase already exist for this invoice?
            existing_case = (
                db.query(RecoveryCase)
                .filter(RecoveryCase.invoice_id == invoice.id)
                .first()
            )

            if existing_case:
                action_taken = "CASE_ALREADY_EXISTS"
                created_case_id = existing_case.id
            else:
                days_overdue = max(1, (now - invoice.due_at).days) if now > invoice.due_at else 1
                outstanding_paise = invoice.amount_paise - invoice.paid_amount_paise

                event_payload = EventCreate(
                    merchant_id=current_merchant.id,
                    customer_id=customer.id,
                    invoice_id=invoice.id,
                    event_type="INVOICE_OVERDUE",
                    amount_paise=outstanding_paise,
                    currency=invoice.currency,
                    failure_reason="B2B invoice remains unpaid after due date",
                    source="merchant_erp",
                    occurred_at=data.occurred_at or now,
                    raw_payload={
                        "event_id": data.event_id,
                        "invoice_id": data.invoice_id,
                        "days_overdue": days_overdue,
                        "total_amount_paise": invoice.amount_paise,
                        "paid_amount_paise": invoice.paid_amount_paise,
                    }
                )

                rev_event, rec_case = ingest_revenue_event(
                    db=db,
                    data=event_payload,
                    merchant_id=current_merchant.id,
                    auto_pipeline=True
                )
                action_taken = "RECOVERY_CASE_CREATED"
                created_case_id = rec_case.id

    elif event_type in ("INVOICE_PAID", "PAID"):
        # Process verified payment from merchant system
        paid_amount = data.paid_amount_paise or data.amount_paise
        invoice.paid_amount_paise = (invoice.paid_amount_paise or 0) + paid_amount
        if invoice.paid_amount_paise >= invoice.amount_paise:
            invoice.status = "PAID"
            invoice.paid_at = now
            action_taken = "INVOICE_FULLY_PAID"
        else:
            invoice.status = "PARTIALLY_PAID"
            action_taken = "INVOICE_PARTIALLY_PAID"

        # Find any active case for this invoice to reconcile
        active_case = (
            db.query(RecoveryCase)
            .filter(RecoveryCase.invoice_id == invoice.id)
            .first()
        )
        if active_case:
            handle_payment_recovered(
                db=db,
                case_id=active_case.id,
                paid_amount_paise=paid_amount,
                payment_id=f"pay_erp_{data.event_id}",
                external_event_id=data.event_id,
            )
            created_case_id = active_case.id

    db.commit()

    return ReceivableEventResponse(
        status="success",
        event_id=data.event_id,
        invoice_id=data.invoice_id,
        internal_invoice_id=invoice.id,
        event_type=event_type,
        action_taken=action_taken,
        case_id=created_case_id,
        processed_at=now,
    )
