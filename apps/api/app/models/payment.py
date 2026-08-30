from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("PAY"))
    order_id = Column(String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    external_payment_id = Column(String, nullable=True, index=True)
    amount_paise = Column(BigInteger, nullable=False)
    status = Column(String, nullable=False)  # FAILED, SUCCESS, PENDING
    method = Column(String, nullable=True)   # card, upi, netbanking
    failure_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    order = relationship("Order", back_populates="payments")
