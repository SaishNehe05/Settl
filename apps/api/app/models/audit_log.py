from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("AUD"))
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(String, ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    actor = Column(String, nullable=False)  # SYSTEM, AGENT, POLICY_ENGINE, HUMAN_OPERATOR, RAZORPAY_WEBHOOK
    event_name = Column(String, nullable=False, index=True)
    reason = Column(Text, nullable=True)
    log_metadata = Column("metadata", JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    # Relationships
    merchant = relationship("Merchant", back_populates="audit_logs")
    recovery_case = relationship("RecoveryCase", back_populates="audit_logs")
