from sqlalchemy import Column, DateTime, ForeignKey, String, Integer
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Promise(Base):
    __tablename__ = "promises"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("PRM"))
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(String, ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True, index=True)
    
    promised_amount_paise = Column(Integer, nullable=False)
    promise_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="PROMISED", nullable=False)  # PROMISED, FULFILLED, PARTIALLY_FULFILLED, BROKEN, CANCELLED
    created_by = Column(String, nullable=True, default="MERCHANT") # System/source that created the promise
    
    fulfilled_amount_paise = Column(Integer, default=0, nullable=False)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)
    broken_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    merchant = relationship("Merchant", back_populates="promises")
    recovery_case = relationship("RecoveryCase", back_populates="promises")
    customer = relationship("Customer", back_populates="promises")
    invoice = relationship("Invoice", back_populates="promises")
