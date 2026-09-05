from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.merchant import Merchant
from app.models.recovery_case import RecoveryCase
from app.models.customer import Customer
from app.schemas.dashboard import DashboardSummary
from app.schemas.recovery_case import RecoveryCaseListItem
from app.api.deps import get_current_merchant

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    mode: Optional[str] = Query(None, description="Filter by mode: 'simulation' or 'api'"),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    cases_query = db.query(RecoveryCase).filter(RecoveryCase.merchant_id == current_merchant.id)
    cases = cases_query.all()
    
    if mode == "simulation":
        cases = [c for c in cases if c.revenue_event and c.revenue_event.source == "synthetic"]
    elif mode == "api":
        cases = [c for c in cases if c.revenue_event and c.revenue_event.source != "synthetic"]
    
    total_cases = len(cases)
    active_cases = len([c for c in cases if c.status not in ["RECOVERED", "STOPPED"]])
    recovered_cases = len([c for c in cases if c.status == "RECOVERED"])
    guardrail_blocks = len([c for c in cases if c.status in ["BLOCKED", "STOPPED"]])
    human_escalations = len([c for c in cases if c.status == "ESCALATED"])
    
    revenue_at_risk = sum(c.amount_at_risk_paise for c in cases)
    # Eligible revenue: cases not blocked by policy eligibility
    eligible_cases = [c for c in cases if c.status != "BLOCKED"]
    eligible_revenue = sum(c.amount_at_risk_paise for c in eligible_cases)
    
    revenue_recovered = sum(c.amount_recovered_paise for c in cases if c.status == "RECOVERED")
    
    simulation_revenue = sum(c.amount_recovered_paise for c in cases if c.status == "RECOVERED" and c.revenue_event and c.revenue_event.source == "synthetic")
    real_revenue = sum(c.amount_recovered_paise for c in cases if c.status == "RECOVERED" and c.revenue_event and c.revenue_event.source != "synthetic")
    
    recovery_attempts = sum(c.attempt_count for c in cases)
    
    recovery_rate = (revenue_recovered / eligible_revenue) if eligible_revenue > 0 else 0.0
    
    # Sort and slice the already filtered cases for the recent cases list
    sorted_cases = sorted(cases, key=lambda x: x.created_at, reverse=True)
    recent_query = sorted_cases[:10]
    
    recent_items = []
    for c in recent_query:
        cust_name = None
        cust_email = None
        if c.revenue_event and c.revenue_event.customer:
            cust_name = c.revenue_event.customer.name
            cust_email = c.revenue_event.customer.email
        
        recent_items.append(
            RecoveryCaseListItem(
                id=c.id,
                merchant_id=c.merchant_id,
                revenue_event_id=c.revenue_event_id,
                amount_at_risk_paise=c.amount_at_risk_paise,
                recovery_probability=c.recovery_probability,
                root_cause=c.root_cause,
                priority=c.priority,
                recommended_action=c.recommended_action,
                actual_action=c.actual_action,
                attempt_count=c.attempt_count,
                status=c.status,
                amount_recovered_paise=c.amount_recovered_paise,
                escalation_status=c.escalation_status,
                customer_name=cust_name,
                customer_email=cust_email,
                source=c.revenue_event.source if c.revenue_event else None,
                subscription_id=c.subscription_id,
                billing_cycle_id=c.billing_cycle_id,
                provider_state=c.provider_state,
                created_at=c.created_at,
                updated_at=c.updated_at
            )
        )
        
    return DashboardSummary(
        revenue_at_risk_paise=revenue_at_risk,
        eligible_revenue_paise=eligible_revenue,
        revenue_recovered_paise=revenue_recovered,
        simulation_revenue_recovered_paise=simulation_revenue,
        real_revenue_recovered_paise=real_revenue,
        recovery_attempts_count=recovery_attempts,
        recovery_rate=round(recovery_rate, 4),
        guardrail_blocks_count=guardrail_blocks,
        human_escalations_count=human_escalations,
        total_cases_count=total_cases,
        active_cases_count=active_cases,
        recovered_cases_count=recovered_cases,
        recent_cases=recent_items
    )

@router.delete("/clear-all")
def clear_all_cases(db: Session = Depends(get_db)):
    # Hidden debug endpoint to wipe the DB for the hackathon
    db.query(RecoveryCase).delete()
    db.commit()
    return {"status": "success", "message": "All cases deleted from live database"}
