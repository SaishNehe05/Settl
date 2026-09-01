from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class EventCreate(BaseModel):
    event_id: Optional[str] = None
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    
    # Customer details if inline
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    
    # Scenario metadata
    scenario_type: Optional[str] = None  # payment_degradation, checkout_dropoff, subscription_failure, etc.
    subscription_id: Optional[str] = None
    mandate_id: Optional[str] = None
    invoice_id: Optional[str] = None
    
    event_type: str = Field(..., description="PAYMENT_FAILED, CHECKOUT_ABANDONED, SUBSCRIPTION_HALTED, MANDATE_BOUNCED, INVOICE_OVERDUE")
    amount_paise: int = Field(..., gt=0, description="Amount in paise (e.g. 849900 for ₹8,499)")
    currency: str = "INR"
    failure_reason: Optional[str] = None
    source: str = "synthetic"  # razorpay, synthetic, merchant_app
    occurred_at: Optional[datetime] = None
    raw_payload: Optional[Dict[str, Any]] = None


class EventResponse(BaseModel):
    id: str
    merchant_id: str
    customer_id: str
    order_id: Optional[str] = None
    event_type: str
    amount_paise: int
    failure_reason: Optional[str] = None
    source: str
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
