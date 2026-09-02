from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PromiseCreate(BaseModel):
    promised_amount_paise: int = Field(..., gt=0)
    promise_date: datetime
    created_by: Optional[str] = "MERCHANT"

class PromiseResponse(BaseModel):
    id: str
    merchant_id: str
    case_id: str
    customer_id: str
    invoice_id: Optional[str]
    promised_amount_paise: int
    promise_date: datetime
    status: str
    created_by: Optional[str]
    fulfilled_amount_paise: int
    fulfilled_at: Optional[datetime]
    broken_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
