from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import json

from app.database import get_db
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.checkout_session import CheckoutSession
from app.models.base import generate_uuid
from app.api.deps import get_current_merchant
from app.config import settings

router = APIRouter(prefix="/checkout", tags=["Checkout"])

class CheckoutEventRequest(BaseModel):
    event: str = Field(..., description="CHECKOUT_STARTED, PAYMENT_ATTEMPTED, PAYMENT_SUCCESS, PAYMENT_FAILED")
    checkout_session_id: str
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    amount_paise: int = Field(..., gt=0)
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    merchant_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/events", status_code=status.HTTP_200_OK)
def ingest_checkout_event(
    req: CheckoutEventRequest,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    """
    Ingests a checkout lifecycle event from the merchant website.
    Updates or creates the CheckoutSession accordingly.
    """
    now = datetime.now(timezone.utc)
    
    # Explicit merchant routing for Demo Store
    if req.merchant_id:
        current_merchant = db.query(Merchant).filter(Merchant.id == req.merchant_id).first()
        if not current_merchant:
            raise HTTPException(404, detail="Merchant not found")

    # 1. Resolve Customer
    customer = None
    if req.customer_id:
        customer = db.query(Customer).filter(Customer.id == req.customer_id, Customer.merchant_id == current_merchant.id).first()
    
    if not customer and (req.customer_name or req.customer_email):
        # Create ad-hoc customer
        customer = Customer(
            id=generate_uuid("CUS"),
            merchant_id=current_merchant.id,
            name=req.customer_name or "Anonymous Customer",
            email=req.customer_email or f"customer_{generate_uuid()}@example.com",
            phone=req.customer_phone or "+919876543210",
            success_rate=0.85, # Note: AI treats new users dynamically
            customer_value="MEDIUM",
            opted_out=False,
        )
        db.add(customer)
        db.flush()

    # 2. Get or Create CheckoutSession
    session_id = req.checkout_session_id
    chk_session = db.query(CheckoutSession).filter(
        CheckoutSession.id == session_id,
        CheckoutSession.merchant_id == current_merchant.id
    ).first()

    if not chk_session:
        # Configurable timeout
        timeout_minutes = settings.CHECKOUT_ABANDONMENT_MINUTES
        deadline = now + timedelta(minutes=timeout_minutes)

        chk_session = CheckoutSession(
            id=session_id,
            merchant_id=current_merchant.id,
            customer_id=customer.id if customer else None,
            order_id=req.order_id,
            amount_paise=req.amount_paise,
            status="STARTED",
            started_at=now,
            last_activity_at=now,
            abandonment_deadline=deadline
        )
        db.add(chk_session)
    else:
        chk_session.last_activity_at = now
        # Refresh deadline (reset the timer since they are still active)
        if req.event in ["CHECKOUT_STARTED", "PAYMENT_ATTEMPTED"]:
            chk_session.abandonment_deadline = now + timedelta(minutes=settings.CHECKOUT_ABANDONMENT_MINUTES)

    # 3. State Machine transitions
    if req.event == "PAYMENT_ATTEMPTED":
        if chk_session.status == "STARTED":
            chk_session.status = "PAYMENT_ATTEMPTED"
        chk_session.payment_attempted_at = now
        
    elif req.event == "PAYMENT_SUCCESS":
        chk_session.status = "PAYMENT_SUCCESS"
        chk_session.payment_succeeded_at = now
        
    elif req.event == "PAYMENT_FAILED":
        # Keep it in PAYMENT_ATTEMPTED state so it can eventually be abandoned or retried
        if chk_session.status == "STARTED":
            chk_session.status = "PAYMENT_ATTEMPTED"

    db.commit()
    db.refresh(chk_session)

    return {
        "status": "success", 
        "checkout_session_id": chk_session.id,
        "state": chk_session.status
    }
