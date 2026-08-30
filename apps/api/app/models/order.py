from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("ORD"))
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    external_order_id = Column(String, nullable=True, index=True)
    amount_paise = Column(BigInteger, nullable=False)  # Money in paise
    currency = Column(String, default="INR", nullable=False)
    status = Column(String, default="PENDING", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    merchant = relationship("Merchant", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    revenue_events = relationship("RevenueEvent", back_populates="order")
