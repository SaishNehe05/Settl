from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class CheckoutSession(Base):
    __tablename__ = "checkout_sessions"

    id = Column(String, primary_key=True)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    order_id = Column(String, nullable=True, index=True)
    
    amount_paise = Column(Integer, nullable=False)
    currency = Column(String, default="INR", nullable=False)
    
    status = Column(String, nullable=False, default="STARTED")  # STARTED, PAYMENT_ATTEMPTED, PAYMENT_SUCCESS, ABANDONED
    
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_activity_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    payment_attempted_at = Column(DateTime, nullable=True)
    payment_succeeded_at = Column(DateTime, nullable=True)
    
    abandonment_deadline = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    merchant = relationship("Merchant", back_populates="checkout_sessions")
    customer = relationship("Customer")

    __table_args__ = (
        Index("ix_checkout_sessions_status_deadline", "status", "abandonment_deadline"),
    )
