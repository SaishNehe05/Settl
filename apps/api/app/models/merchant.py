from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("MER"))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    api_key_hash = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    customers = relationship("Customer", back_populates="merchant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="merchant", cascade="all, delete-orphan")
    revenue_events = relationship("RevenueEvent", back_populates="merchant", cascade="all, delete-orphan")
    recovery_cases = relationship("RecoveryCase", back_populates="merchant", cascade="all, delete-orphan")
    policy = relationship("Policy", back_populates="merchant", uselist=False, cascade="all, delete-orphan")
    checkout_sessions = relationship("CheckoutSession", back_populates="merchant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="merchant", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="merchant", cascade="all, delete-orphan")
