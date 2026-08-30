from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("ACT"))
    case_id = Column(String, ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String, nullable=False)  # CREATE_PAYMENT_LINK, SEND_PAYMENT_LINK, SEND_REMINDER, WAIT, ESCALATE, STOP
    status = Column(String, default="PENDING", nullable=False)  # PENDING, SUCCESS, FAILED, BLOCKED
    
    razorpay_entity_id = Column(String, nullable=True, index=True)
    reference_id = Column(String, unique=True, nullable=True, index=True)
    
    policy_result = Column(String, nullable=True)  # ALLOW, ESCALATE, STOP, BLOCK, WAIT
    policy_reason = Column(String, nullable=True)
    
    request_payload = Column(JSON, nullable=True)
    response_payload = Column(JSON, nullable=True)
    executed_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="recovery_actions")
