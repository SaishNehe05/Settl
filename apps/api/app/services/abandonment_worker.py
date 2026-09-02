import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.checkout_session import CheckoutSession
from app.models.base import generate_uuid
from app.schemas.event import EventCreate
from app.services.event_service import ingest_revenue_event

logger = logging.getLogger(__name__)

async def abandonment_worker_loop():
    """
    Background worker that periodically checks for abandoned checkout sessions.
    """
    logger.info("Starting checkout abandonment worker...")
    while True:
        try:
            process_abandoned_checkouts()
        except Exception as e:
            logger.error(f"Error in abandonment worker: {e}")
        await asyncio.sleep(15)  # Run every 15 seconds

def process_abandoned_checkouts():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        # Find sessions that have expired but are not yet marked ABANDONED or SUCCESS
        expired_sessions = db.query(CheckoutSession).filter(
            CheckoutSession.status.in_(["STARTED", "PAYMENT_ATTEMPTED"]),
            CheckoutSession.abandonment_deadline <= now
        ).all()
        
        if not expired_sessions:
            return

        for chk_session in expired_sessions:
            try:
                # 1. Update status to ABANDONED
                chk_session.status = "ABANDONED"
                db.flush()

                # 2. Create normalized RevenueEvent (which triggers the recovery pipeline)
                event_id = generate_uuid("EVT")
                customer = chk_session.customer

                event_data = EventCreate(
                    event_id=event_id,
                    customer_name=customer.name if customer else "Anonymous Customer",
                    customer_email=customer.email if customer else "customer@example.com",
                    customer_phone=customer.phone if customer else "+919876543210",
                    event_type="CHECKOUT_ABANDONED",
                    amount_paise=chk_session.amount_paise,
                    failure_reason="checkout_session_abandoned",
                    source="checkout_lifecycle",
                    scenario_type="checkout_dropoff",
                    raw_payload={
                        "checkout_session_id": chk_session.id,
                        "order_id": chk_session.order_id,
                        "last_activity_at": chk_session.last_activity_at.isoformat()
                    }
                )

                ingest_revenue_event(
                    db=db,
                    data=event_data,
                    merchant_id=chk_session.merchant_id,
                    auto_pipeline=True
                )
                
                db.commit()
                logger.info(f"Processed abandoned checkout session: {chk_session.id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to process checkout {chk_session.id}: {e}")

    finally:
        db.close()
