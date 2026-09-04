from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import razorpay
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.merchant import Merchant
from app.config import settings

router = APIRouter(prefix="/demo", tags=["Demo Store"])

class CreateOrderRequest(BaseModel):
    amount_paise: int
    currency: str = "INR"
    receipt: str = "demo_receipt"
    merchant_id: str

@router.post("/create-order")
def create_demo_order(req: CreateOrderRequest, db: Session = Depends(get_db)):
    """
    Creates a Razorpay Order for the Demo Store checkout.
    """
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Razorpay credentials not configured in backend."
        )

    # Fetch the exact merchant that the demo store is testing with
    merchant = db.query(Merchant).filter(Merchant.id == req.merchant_id).first()
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {req.merchant_id} not found."
        )

    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order_data = {
            "amount": req.amount_paise,
            "currency": req.currency,
            "receipt": req.receipt,
            "payment_capture": 1 # Auto capture
        }
        order = client.order.create(data=order_data)
        
        return {
            "status": "success",
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": settings.RAZORPAY_KEY_ID,
            "merchant_id": merchant.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Razorpay Order: {str(e)}"
        )
