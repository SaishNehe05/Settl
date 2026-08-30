from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, default=lambda: generate_uuid("POL"))
    merchant_id = Column(String, ForeignKey("merchants.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    max_attempts = Column(Integer, default=2, nullable=False)
    max_automated_amount_paise = Column(BigInteger, default=1000000, nullable=False)  # ₹10,000 in paise
    min_probability = Column(Float, default=0.40, nullable=False)
    cooldown_minutes = Column(Integer, default=240, nullable=False)
    human_review_above_paise = Column(BigInteger, default=1000000, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    merchant = relationship("Merchant", back_populates="policy")
