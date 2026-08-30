from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    merchant_id: str
    merchant_name: str


class TokenData(BaseModel):
    merchant_id: Optional[str] = None
    email: Optional[str] = None


class MerchantLogin(BaseModel):
    email: EmailStr
    password: str


class MerchantRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class MerchantResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
