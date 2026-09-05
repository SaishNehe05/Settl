import logging
import resend
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.config import settings
from app.models.notification import Notification

logger = logging.getLogger(__name__)

# Initialize resend with the API key from settings
if settings.RESEND_API_KEY:
    resend.api_key = settings.RESEND_API_KEY

def send_email_notification(db: Session, notification: Notification) -> Notification:
    """
    Sends an email using Resend and updates the Notification record status.
    """
    if not settings.RESEND_API_KEY:
        logger.error("RESEND_API_KEY not configured. Cannot send email.")
        notification.status = "FAILED"
        notification.failure_reason = "RESEND_API_KEY not configured"
        db.commit()
        return notification

    # Guard against sending to unknown recipient
    if not notification.recipient or notification.recipient.lower() == "unknown":
        logger.warning(f"Notification {notification.id} has invalid recipient. Failing it.")
        notification.status = "FAILED"
        notification.failure_reason = "Invalid recipient address"
        db.commit()
        return notification

    # Determine subject based on message type
    subject = "Payment Reminder from Settl"
    if notification.message_type == "PROMISE_REMINDER":
        subject = "Action Required: Your Promised Payment is Due"
    elif notification.message_type == "INVOICE_REMINDER":
        subject = "Payment Reminder for your recent Invoice"

    try:
        response = resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": notification.recipient,
            "subject": subject,
            "text": notification.content,
        })
        
        # If response contains 'id', it was successfully submitted to Resend
        if response and "id" in response:
            notification.status = "SENT"
            notification.provider_reference = response["id"]
            notification.sent_at = datetime.now(timezone.utc)
            logger.info(f"Successfully sent email to {notification.recipient}. Resend ID: {response['id']}")
        else:
            notification.status = "FAILED"
            notification.failure_reason = "No ID returned from Resend"
            logger.error(f"Resend email failed: No ID returned. Response: {response}")

    except Exception as e:
        notification.status = "FAILED"
        notification.failure_reason = str(e)
        logger.error(f"Failed to send email via Resend: {str(e)}")

    db.commit()
    db.refresh(notification)
    return notification
