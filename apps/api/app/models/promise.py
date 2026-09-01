from sqlalchemy import Column, DateTime, ForeignKey, String, Integer
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Promise(Base):
    __tablename__ = "promises"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("PRM"))
    case_id = Column(String, ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    promised_amount_paise = Column(Integer, nullable=False)
    promise_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="PROMISED", nullable=False)  # PROMISED, DUE, PAID, BROKEN, ESCALATED
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="promises")
    customer = relationship("Customer", back_populates="promises")
