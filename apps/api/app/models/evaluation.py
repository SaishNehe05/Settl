from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, BigInteger, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("EVAL"))
    dataset_version = Column(String, nullable=False)
    dataset_size = Column(Integer, nullable=False)
    model_version = Column(String, nullable=False)
    policy_version = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now)
    
    # Aggregated Metrics stored as JSON
    metrics = Column(JSON, nullable=False)
    status = Column(String, default="COMPLETED", nullable=False)

    traces = relationship("EvaluationTrace", back_populates="run", cascade="all, delete-orphan")


class EvaluationTrace(Base):
    __tablename__ = "evaluation_traces"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("TRC"))
    run_id = Column(String, ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    customer_success_rate = Column(Float, nullable=False)
    
    # Ground truth (Nullable for real data evaluation)
    ground_truth_recoverable = Column(Boolean, nullable=True)
    ground_truth_ideal_action = Column(String, nullable=True)
    ground_truth_scenario = Column(String, nullable=True)
    
    # Settl AI/Policy
    settl_recommended_action = Column(String, nullable=True)
    policy_decision = Column(String, nullable=True) # ALLOW, STOP, ESCALATE, WAIT
    policy_reason = Column(String, nullable=True)
    actual_action_taken = Column(String, nullable=True)
    
    # Outcomes
    simulated_outcome = Column(String, nullable=False) # RECOVERED, FAILED, STOPPED, ESCALATED
    is_decision_correct = Column(Boolean, nullable=True)
    is_escalation_correct = Column(Boolean, nullable=True)
    policy_violation = Column(Boolean, default=False, nullable=False)
    duplicate_action = Column(Boolean, default=False, nullable=False)
    unauthorized_action = Column(Boolean, default=False, nullable=False)
    
    run = relationship("EvaluationRun", back_populates="traces")
