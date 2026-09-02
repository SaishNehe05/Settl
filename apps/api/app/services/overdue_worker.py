import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.invoice import Invoice
from app.models.recovery_case import RecoveryCase
from app.schemas.event import EventCreate
from app.services.event_service import ingest_revenue_event

logger = logging.getLogger(__name__)

async def detect_overdue_invoices():
    """
    Background worker that runs periodically to detect overdue invoices.
    It provisions an INVOICE_OVERDUE event if one hasn't been created
    for the specific invoice yet.
    """
    while True:
        try:
            # We run the detection synchronously inside the async loop
            await asyncio.to_thread(_process_overdue_invoices)
        except Exception as e:
            logger.error(f"Error in overdue invoice detection worker: {str(e)}")
            
        # Run every 60 seconds
        await asyncio.sleep(60)

def _process_overdue_invoices():
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        # Find invoices that are overdue and not fully paid/voided
        overdue_invoices = (
            db.query(Invoice)
            .filter(
                Invoice.due_at <= now,
                Invoice.paid_amount_paise < Invoice.amount_paise,
                Invoice.status.notin_(["PAID", "VOID"])
            )
            .all()
        )
        
        for invoice in overdue_invoices:
            # Check idempotency: does a RecoveryCase already exist for this invoice?
            existing_case = (
                db.query(RecoveryCase)
                .filter(RecoveryCase.invoice_id == invoice.id)
                .first()
            )
            
            if not existing_case:
                # 1. Update invoice status to OVERDUE if it's not PARTIALLY_PAID
                if invoice.status != "PARTIALLY_PAID":
                    invoice.status = "OVERDUE"
                
                # 2. Create the RevenueEvent payload for the overdue state
                event_payload = EventCreate(
                    merchant_id=invoice.merchant_id,
                    customer_id=invoice.customer_id,
                    invoice_id=invoice.id,
                    event_type="INVOICE_OVERDUE",
                    amount_paise=invoice.amount_paise - invoice.paid_amount_paise,
                    currency=invoice.currency,
                    failure_reason="B2B invoice is overdue past its terms",
                    source="receivable_monitor",
                    occurred_at=now,
                    raw_payload={"days_overdue": (now - invoice.due_at).days}
                )
                
                # 3. Ingest event which automatically provisions the RecoveryCase and runs AI + Policy
                logger.info(f"Dispatching INVOICE_OVERDUE event for invoice {invoice.id}")
                ingest_revenue_event(db=db, data=event_payload, merchant_id=invoice.merchant_id, auto_pipeline=True)
                
        db.commit()
    except Exception as e:
        logger.error(f"Database error while processing overdue invoices: {str(e)}")
        db.rollback()
    finally:
        db.close()
