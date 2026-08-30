from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("NOTIF"))
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(String, ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=True, index=True)
    
    channel = Column(String, nullable=False)  # SMS, EMAIL, WHATSAPP, WEBHOOK
    recipient = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String, default="SENT", nullable=False)  # SENT, DELIVERED, FAILED
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    merchant = relationship("Merchant", back_populates="notifications")
