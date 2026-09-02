from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("CASE"))
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    revenue_event_id = Column(String, ForeignKey("revenue_events.id", ondelete="CASCADE"), unique=True, nullable=False)
    invoice_id = Column(String, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True, index=True)
    subscription_id = Column(String, nullable=True, index=True)
    billing_cycle_id = Column(String, nullable=True, index=True)
    provider_state = Column(String, nullable=True)
    
    amount_at_risk_paise = Column(BigInteger, nullable=False)
    recovery_probability = Column(Float, default=0.0)
    root_cause = Column(String, nullable=True)
    priority = Column(String, default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, URGENT
    
    recommended_action = Column(String, nullable=True)  # CREATE_PAYMENT_LINK, SEND_PAYMENT_LINK, SEND_REMINDER, WAIT, ESCALATE, STOP
    actual_action = Column(String, nullable=True)
    attempt_count = Column(Integer, default=0, nullable=False)
    
    # State machine: NEW -> ANALYZING -> READY -> POLICY_CHECK -> (APPROVED / BLOCKED / ESCALATED) -> EXECUTING -> WAITING_RESULT -> (RECOVERED / FAILED / STOPPED)
    status = Column(String, default="NEW", nullable=False, index=True)
    amount_recovered_paise = Column(BigInteger, default=0, nullable=False)
    escalation_status = Column(String, nullable=True)  # PENDING_REVIEW, APPROVED, REJECTED
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    merchant = relationship("Merchant", back_populates="recovery_cases")
    revenue_event = relationship("RevenueEvent", back_populates="recovery_case")
    invoice = relationship("Invoice")
    recovery_actions = relationship("RecoveryAction", back_populates="recovery_case", cascade="all, delete-orphan", order_by="RecoveryAction.executed_at.desc()")
    audit_logs = relationship("AuditLog", back_populates="recovery_case", cascade="all, delete-orphan", order_by="AuditLog.created_at")
    model_predictions = relationship("ModelPrediction", back_populates="recovery_case", cascade="all, delete-orphan")
    promises = relationship("Promise", back_populates="recovery_case", cascade="all, delete-orphan")
