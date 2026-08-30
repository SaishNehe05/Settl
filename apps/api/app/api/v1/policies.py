from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.merchant import Merchant
from app.models.policy import Policy
from app.schemas.policy import PolicyResponse, PolicyUpdate
from app.api.deps import get_current_merchant

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.get("", response_model=PolicyResponse)
def get_merchant_policy(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    policy = db.query(Policy).filter(Policy.merchant_id == current_merchant.id).first()
    if not policy:
        # Create default policy if none exists
        policy = Policy(merchant_id=current_merchant.id)
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy


@router.patch("", response_model=PolicyResponse)
def update_merchant_policy(
    update_data: PolicyUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    policy = db.query(Policy).filter(Policy.merchant_id == current_merchant.id).first()
    if not policy:
        policy = Policy(merchant_id=current_merchant.id)
        db.add(policy)

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(policy, field, value)

    db.commit()
    db.refresh(policy)
    return policy
