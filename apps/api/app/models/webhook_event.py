from sqlalchemy import Boolean, Column, DateTime, JSON, String, Text, UniqueConstraint
from app.database import Base
from app.models.base import generate_uuid, utc_now


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("WH"))
    provider = Column(String, default="razorpay", nullable=False, index=True)
    external_event_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)  # Original provider event type (e.g. payment.failed)
    settl_event_type = Column(String, nullable=True, index=True)  # Normalized Settl type (e.g. PAYMENT_FAILURE)

    # Merchant / account context
    merchant_id = Column(String, nullable=True, index=True)  # Resolved Settl merchant
    account_id = Column(String, nullable=True, index=True)  # Razorpay account_id from payload

    signature_valid = Column(Boolean, default=False, nullable=False)
    payload = Column(JSON, nullable=False)

    # Processing lifecycle
    received_at = Column(DateTime(timezone=True), default=utc_now)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="RECEIVED", nullable=False, index=True)
    # RECEIVED -> NORMALIZED -> PROCESSING -> PROCESSED | PROCESSING_FAILED | DUPLICATE | IGNORED | UNHANDLED
    processing_error = Column(Text, nullable=True)

    # Link to downstream Settl event created from this webhook
    settl_event_id = Column(String, nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint("provider", "external_event_id", name="uq_provider_external_event_id"),
    )
