"""
Settl Razorpay Webhook Endpoint

Receives, verifies, deduplicates, persists, classifies, and normalizes
incoming Razorpay webhook events. Processing is deferred to a background task.

This handler does NOT:
- Run AI analysis
- Create payment links
- Send notifications
- Execute recovery actions

It IS:
- The authoritative entry point for real Razorpay events
- A durable ingestion boundary with fast HTTP response
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.webhook_event import WebhookEvent
from app.models.base import generate_uuid
from app.services.razorpay_service import verify_razorpay_webhook_signature
from app.services.webhook_classifier import classify_event
from app.services.webhook_normalizer import normalize_webhook_payload
from app.services.webhook_processor import process_webhook

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/razorpay", status_code=status.HTTP_200_OK)
async def handle_razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db),
):
    """
    Receives, verifies, and durably persists incoming Razorpay webhook events.
    Processing is deferred to a background task after the HTTP response.

    Flow:
    1. Read raw body bytes (before any JSON parsing)
    2. Validate X-Razorpay-Signature via HMAC-SHA256
    3. Parse JSON payload
    4. Idempotency check (deduplicate by provider + external_event_id)
    5. Persist raw webhook event (durable evidence)
    6. Classify + normalize event
    7. Queue background processing
    8. Return 200 immediately
    """

    # ── 1. Read raw body ─────────────────────────────────────────────
    raw_body = await request.body()

    # ── 2. Signature verification ────────────────────────────────────
    if not x_razorpay_signature:
        logger.warning("Webhook rejected: missing X-Razorpay-Signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header",
        )

    is_valid = verify_razorpay_webhook_signature(raw_body, x_razorpay_signature)
    if not is_valid:
        logger.warning("WEBHOOK SIGNATURE: INVALID")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )
    logger.info("WEBHOOK SIGNATURE: VALID")

    # ── 3. Parse JSON payload ────────────────────────────────────────
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"Webhook rejected: malformed JSON — {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {str(e)}",
        )

    # Extract event identifiers
    external_event_id = payload.get("event_id") or payload.get("id") or generate_uuid("WH_EVT")
    razorpay_event_type = payload.get("event", "unknown")
    account_id = payload.get("account_id")

    # ── 4. Idempotency / duplicate protection ────────────────────────
    existing_wh = (
        db.query(WebhookEvent)
        .filter(
            WebhookEvent.provider == "razorpay",
            WebhookEvent.external_event_id == external_event_id,
        )
        .first()
    )
    
    logger.info(f"RAZORPAY WEBHOOK RECEIVED\nevent={razorpay_event_type}\nexternal_event_id={external_event_id}")

    if existing_wh:
        logger.info(f"EVENT DEDUPLICATION:\nDUPLICATE\nexisting_event_id={external_event_id}")
        return {
            "status": "already_processed",
            "event_id": external_event_id,
            "webhook_id": existing_wh.id,
        }
    logger.info("EVENT DEDUPLICATION:\nNEW")

    # ── 5. Classify event ────────────────────────────────────────────
    settl_event_type = classify_event(razorpay_event_type)

    # ── 6. Persist raw webhook event (durable evidence) ──────────────
    wh = WebhookEvent(
        provider="razorpay",
        external_event_id=external_event_id,
        event_type=razorpay_event_type,
        settl_event_type=settl_event_type,
        account_id=account_id,
        signature_valid=True,
        payload=payload,
        status="RECEIVED",
        received_at=datetime.now(timezone.utc),
    )

    try:
        db.add(wh)
        db.commit()
        db.refresh(wh)
        logger.info(f"WEBHOOK EVENT PERSISTED\nexternal_event_id={external_event_id}")
    except IntegrityError as e:
        # Race condition: another request persisted the same event between our check and insert
        db.rollback()
        logger.error(f"WEBHOOK EVENT PERSISTENCE FAILED (IntegrityError): {e}")
        return {
            "status": "already_processed",
            "event_id": external_event_id,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"WEBHOOK EVENT PERSISTENCE FAILED: {e}")
        raise

    # ── 7. Queue background processing ───────────────────────────────
    logger.info(f"EVENT QUEUED\nevent_id={external_event_id}")
    background_tasks.add_task(process_webhook, wh.id)

    # ── 8. Return fast response ──────────────────────────────────────
    return {
        "status": "received",
        "webhook_id": wh.id,
        "event_id": external_event_id,
        "event_type": razorpay_event_type,
        "settl_event_type": settl_event_type,
    }
