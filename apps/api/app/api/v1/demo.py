from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import razorpay
from app.config import settings

router = APIRouter(prefix="/demo", tags=["Demo Store"])

class CreateOrderRequest(BaseModel):
    amount_paise: int
    currency: str = "INR"
    receipt: str = "demo_receipt"

@router.post("/create-order")
def create_demo_order(req: CreateOrderRequest):
    """
    Creates a Razorpay Order for the Demo Store checkout.
    """
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Razorpay credentials not configured in backend."
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
            "key_id": settings.RAZORPAY_KEY_ID # Needed by frontend to initialize Razorpay Checkout
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Razorpay Order: {str(e)}"
        )
