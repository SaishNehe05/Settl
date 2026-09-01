from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("CUS"))
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    external_customer_id = Column(String, nullable=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    success_rate = Column(Float, default=1.0)
    customer_value = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH
    opted_out = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    merchant = relationship("Merchant", back_populates="customers")
    orders = relationship("Order", back_populates="customer")
    revenue_events = relationship("RevenueEvent", back_populates="customer", cascade="all, delete-orphan")
    promises = relationship("Promise", back_populates="customer", cascade="all, delete-orphan")
