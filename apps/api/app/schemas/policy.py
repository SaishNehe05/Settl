from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PolicyResponse(BaseModel):
    id: str
    merchant_id: str
    max_attempts: int
    max_automated_amount_paise: int
    min_probability: float
    cooldown_minutes: int
    human_review_above_paise: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyUpdate(BaseModel):
    max_attempts: Optional[int] = Field(None, ge=1, le=10)
    max_automated_amount_paise: Optional[int] = Field(None, gt=0)
    min_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    cooldown_minutes: Optional[int] = Field(None, ge=0)
    human_review_above_paise: Optional[int] = Field(None, gt=0)
