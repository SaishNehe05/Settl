"""
Settl Webhook Retry Worker

Periodic background worker that retries processing for webhook events
that failed or got stuck. Registered in main.py lifespan.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.database import SessionLocal
from app.models.webhook_event import WebhookEvent
from app.services.webhook_processor import process_webhook

logger = logging.getLogger(__name__)

RETRY_INTERVAL_SECONDS = 60
MAX_WEBHOOK_AGE_HOURS = 24
RETRYABLE_STATUSES = ("RECEIVED", "NORMALIZED", "PROCESSING_FAILED")


async def webhook_retry_worker():
    """
    Background worker that periodically checks for stuck or failed webhook events
    and retries processing them. Runs in the FastAPI lifespan loop.
    """
    logger.info("Webhook retry worker started")
    while True:
        try:
            await asyncio.to_thread(_retry_pending_webhooks)
        except Exception as e:
            logger.error(f"Webhook retry worker error: {e}", exc_info=True)

        await asyncio.sleep(RETRY_INTERVAL_SECONDS)


def _retry_pending_webhooks():
    """Synchronous retry logic — runs in a thread."""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_WEBHOOK_AGE_HOURS)

        pending = (
            db.query(WebhookEvent)
            .filter(
                WebhookEvent.status.in_(RETRYABLE_STATUSES),
                WebhookEvent.received_at >= cutoff,
            )
            .order_by(WebhookEvent.received_at.asc())
            .limit(20)
            .all()
        )

        if pending:
            logger.info(f"Webhook retry worker: found {len(pending)} webhooks to retry")

        for wh in pending:
            try:
                logger.info(f"Retrying webhook {wh.id} (status={wh.status}, type={wh.event_type})")
                process_webhook(wh.id)
            except Exception as e:
                logger.error(f"Retry failed for webhook {wh.id}: {e}")

    except Exception as e:
        logger.error(f"Webhook retry scan error: {e}", exc_info=True)
    finally:
        db.close()
