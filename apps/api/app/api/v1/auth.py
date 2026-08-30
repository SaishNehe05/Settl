from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.merchant import Merchant
from app.models.policy import Policy
from app.schemas.auth import Token, MerchantLogin, MerchantRegister, MerchantResponse
from app.services.auth_service import verify_password, get_password_hash, create_access_token
from app.api.deps import get_current_merchant

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token)
def register(data: MerchantRegister, db: Session = Depends(get_db)):
    existing = db.query(Merchant).filter(Merchant.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    merchant = Merchant(
        name=data.name,
        email=data.email,
        password_hash=get_password_hash(data.password)
    )
    db.add(merchant)
    db.flush()

    # Create default policy for merchant
    policy = Policy(merchant_id=merchant.id)
    db.add(policy)
    db.commit()
    db.refresh(merchant)

    token = create_access_token(data={"sub": merchant.id, "email": merchant.email})
    return Token(
        access_token=token,
        token_type="bearer",
        merchant_id=merchant.id,
        merchant_name=merchant.name
    )


@router.post("/login", response_model=Token)
def login(data: MerchantLogin, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.email == data.email).first()
    if not merchant or not verify_password(data.password, merchant.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": merchant.id, "email": merchant.email})
    return Token(
        access_token=token,
        token_type="bearer",
        merchant_id=merchant.id,
        merchant_name=merchant.name
    )


@router.get("/me", response_model=MerchantResponse)
def get_me(current_merchant: Merchant = Depends(get_current_merchant)):
    return current_merchant
