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


class SimulateRequest(BaseModel):
    scenario: str = "clean_recovery"  # clean_recovery, high_value, max_attempts, opt_out, low_prob
    amount_paise: Optional[int] = None
    customer_name: Optional[str] = None


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


@router.post("/simulate", response_model=IngestResponse)
def simulate_event(
    req: SimulateRequest,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    """
    Convenience endpoint for judges and testers to inject simulated events across different scenarios.
    """
    scenarios = {
        "payment_degradation": {
            "amount": 849900,
            "reason": "temporary_bank_failure",
            "name": "Arjun Mehta",
            "email": "arjun.mehta@example.com",
            "type": "PAYMENT_FAILED",
            "scenario_tag": "payment_degradation",
        },
        "checkout_dropoff": {
            "amount": 320000,
            "reason": "checkout_session_abandoned",
            "name": "Diya Mukherjee",
            "email": "diya.mukherjee@example.com",
            "type": "CHECKOUT_ABANDONED",
            "scenario_tag": "checkout_dropoff",
        },
        "subscription_failure": {
            "amount": 99900,
            "reason": "subscription_renewal_declined",
            "name": "Vivaan Patel",
            "email": "vivaan.patel@example.com",
            "type": "SUBSCRIPTION_HALTED",
            "scenario_tag": "subscription_failure",
        },
        "b2b_receivables": {
            "amount": 7500000,
            "reason": "invoice_overdue_net30",
            "name": "Kapoor Industries Pvt Ltd",
            "email": "accounts@kapoorindustries.in",
            "type": "INVOICE_OVERDUE",
            "scenario_tag": "b2b_receivables",
        },
        "mandate_retry": {
            "amount": 150000,
            "reason": "emandate_nach_bounce",
            "name": "Saanvi Rao",
            "email": "saanvi.rao@example.com",
            "type": "MANDATE_BOUNCED",
            "scenario_tag": "mandate_retry",
        },
        "hinglish_voice": {
            "amount": 249900,
            "reason": "regional_hinglish_voice_recovery",
            "name": "Ramesh Kumar",
            "email": "ramesh.kumar@example.com",
            "type": "PAYMENT_FAILED",
            "scenario_tag": "hinglish_voice",
        },
        "promise_to_pay": {
            "amount": 450000,
            "reason": "promise_acknowledged_will_pay",
            "name": "Aadhya Menon",
            "email": "aadhya.menon@example.com",
            "type": "PAYMENT_FAILED",
            "scenario_tag": "promise_to_pay",
        },
        # Legacy aliases for backward compatibility
        "clean_recovery": {
            "amount": 849900,
            "reason": "temporary_bank_failure",
            "name": "Arjun Mehta",
            "email": "arjun.mehta@example.com",
            "type": "PAYMENT_FAILED",
            "scenario_tag": "payment_degradation",
        },
        "high_value": {
            "amount": 4500000,
            "reason": "gateway_timeout",
            "name": "Sunita Rao",
            "email": "sunita.rao@example.com",
            "type": "PAYMENT_FAILED",
            "scenario_tag": "payment_degradation",
        },
        "opt_out": {
            "amount": 650000,
            "reason": "session_timeout",
            "name": "Priya Nair",
            "email": "priya.nair@example.com",
            "type": "CHECKOUT_ABANDONED",
            "scenario_tag": "checkout_dropoff",
        },
        "low_prob": {
            "amount": 320000,
            "reason": "card_expired",
            "name": "Karan Kapoor",
            "email": "karan.kapoor@example.com",
            "type": "PAYMENT_FAILED",
            "scenario_tag": "payment_degradation",
        },
    }

    sc = scenarios.get(req.scenario, scenarios["payment_degradation"])
    amount = req.amount_paise or sc["amount"]
    name = req.customer_name or sc["name"]

    data = EventCreate(
        event_id=generate_uuid("EVT_SIM"),
        customer_name=name,
        customer_email=sc["email"],
        customer_phone="+919876543210",
        event_type=sc["type"],
        amount_paise=amount,
        failure_reason=sc["reason"],
        source="synthetic",
        scenario_type=sc.get("scenario_tag", req.scenario),
        raw_payload={"scenario": req.scenario, "scenario_type": sc.get("scenario_tag", req.scenario), "simulated": True},
    )

    event, case = ingest_revenue_event(
        db=db,
        data=data,
        merchant_id=current_merchant.id,
        auto_pipeline=True,
    )

    cust_name = event.customer.name if event.customer else name
    cust_email = event.customer.email if event.customer else sc["email"]

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
