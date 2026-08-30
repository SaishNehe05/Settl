from sqlalchemy import Boolean, Column, DateTime, JSON, String, UniqueConstraint
from app.database import Base
from app.models.base import generate_uuid, utc_now


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("WH"))
    provider = Column(String, default="razorpay", nullable=False, index=True)
    external_event_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    
    signature_valid = Column(Boolean, default=False, nullable=False)
    payload = Column(JSON, nullable=False)
    
    received_at = Column(DateTime(timezone=True), default=utc_now)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="PENDING", nullable=False)  # PENDING, PROCESSED, IGNORED, FAILED

    __table_args__ = (
        UniqueConstraint("provider", "external_event_id", name="uq_provider_external_event_id"),
    )
