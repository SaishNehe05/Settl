from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class RevenueEvent(Base):
    __tablename__ = "revenue_events"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("EVT"))
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type = Column(String, nullable=False, index=True)  # PAYMENT_FAILED, CHECKOUT_ABANDONED, SUBSCRIPTION_HALTED
    amount_paise = Column(BigInteger, nullable=False)
    failure_reason = Column(String, nullable=True)
    source = Column(String, default="synthetic", nullable=False)  # razorpay, synthetic, merchant_app
    occurred_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    merchant = relationship("Merchant", back_populates="revenue_events")
    customer = relationship("Customer", back_populates="revenue_events")
    order = relationship("Order", back_populates="revenue_events")
    recovery_case = relationship("RecoveryCase", back_populates="revenue_event", uselist=False, cascade="all, delete-orphan")
