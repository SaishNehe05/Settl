from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.merchant import Merchant
from app.models.base import generate_uuid
from app.schemas.event import EventCreate, EventResponse
from app.schemas.recovery_case import RecoveryCaseListItem
from app.services.event_service import ingest_revenue_event
from app.api.deps import get_current_merchant

router = APIRouter(prefix="/events", tags=["Revenue Events"])


class IngestResponse(BaseModel):
    event: EventResponse
    case: RecoveryCaseListItem





@router.post("", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_event(
    data: EventCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    event, case = ingest_revenue_event(
        db=db,
        data=data,
        merchant_id=current_merchant.id,
        auto_pipeline=True,
    )
    
    cust_name = event.customer.name if event.customer else None
    cust_email = event.customer.email if event.customer else None

    return IngestResponse(
        event=EventResponse.model_validate(event),
        case=RecoveryCaseListItem(
            id=case.id,
            merchant_id=case.merchant_id,
            revenue_event_id=case.revenue_event_id,
            amount_at_risk_paise=case.amount_at_risk_paise,
            recovery_probability=case.recovery_probability,
            root_cause=case.root_cause,
            priority=case.priority,
            recommended_action=case.recommended_action,
            actual_action=case.actual_action,
            attempt_count=case.attempt_count,
            status=case.status,
            amount_recovered_paise=case.amount_recovered_paise,
            escalation_status=case.escalation_status,
            customer_name=cust_name,
            customer_email=cust_email,
            created_at=case.created_at,
            updated_at=case.updated_at,
        ),
    )




