from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("INV"))
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    external_invoice_id = Column(String, nullable=True, index=True)
    
    amount_paise = Column(BigInteger, nullable=False)
    paid_amount_paise = Column(BigInteger, default=0, nullable=False)
    currency = Column(String, default="INR", nullable=False)
    
    issued_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # DRAFT, ISSUED, DUE, OVERDUE, PARTIALLY_PAID, PAID, VOID
    status = Column(String, default="ISSUED", nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    merchant = relationship("Merchant", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    promises = relationship("Promise", back_populates="invoice", cascade="all, delete-orphan")
    revenue_events = relationship("RevenueEvent", back_populates="invoice")
