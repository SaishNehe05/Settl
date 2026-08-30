from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("PRED"))
    case_id = Column(String, ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    probability = Column(Float, nullable=False)
    root_cause_prediction = Column(String, nullable=True)
    recommended_action = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    features_hash = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="model_predictions")
