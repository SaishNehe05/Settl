from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.merchant import Merchant
from app.models.recovery_case import RecoveryCase
from app.models.model_prediction import ModelPrediction
from app.schemas.recovery_case import (
    RecoveryCaseListItem,
    RecoveryCaseDetail,
    RecoveryActionResponse,
    AuditLogResponse,
    CustomerResponse,
    ModelPredictionResponse,
)
from app.api.deps import get_current_merchant

router = APIRouter(prefix="/recovery-cases", tags=["Recovery Cases"])


@router.get("", response_model=List[RecoveryCaseListItem])
def list_recovery_cases(
    status: Optional[str] = Query(None, description="Filter by case status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    query = db.query(RecoveryCase).filter(RecoveryCase.merchant_id == current_merchant.id)
    if status:
        query = query.filter(RecoveryCase.status == status)
    if priority:
        query = query.filter(RecoveryCase.priority == priority)
        
    cases = query.order_by(RecoveryCase.created_at.desc()).offset(offset).limit(limit).all()
    
    items = []
    for c in cases:
        cust_name = None
        cust_email = None
        if c.revenue_event and c.revenue_event.customer:
            cust_name = c.revenue_event.customer.name
            cust_email = c.revenue_event.customer.email
            
        items.append(
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
                created_at=c.created_at,
                updated_at=c.updated_at
            )
        )
    return items


@router.get("/{case_id}", response_model=RecoveryCaseDetail)
def get_recovery_case(
    case_id: str,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    c = db.query(RecoveryCase).filter(
        RecoveryCase.id == case_id,
        RecoveryCase.merchant_id == current_merchant.id
    ).first()
    
    if not c:
        raise HTTPException(status_code=404, detail="Recovery case not found")
        
    customer_resp = None
    event_type = None
    failure_reason = None
    
    if c.revenue_event:
        event_type = c.revenue_event.event_type
        failure_reason = c.revenue_event.failure_reason
        if c.revenue_event.customer:
            cust = c.revenue_event.customer
            customer_resp = CustomerResponse(
                id=cust.id,
                name=cust.name,
                email=cust.email,
                phone=cust.phone,
                success_rate=cust.success_rate,
                customer_value=cust.customer_value,
                opted_out=cust.opted_out
            )
            
    actions = [
        RecoveryActionResponse(
            id=a.id,
            action_type=a.action_type,
            status=a.status,
            razorpay_entity_id=a.razorpay_entity_id,
            reference_id=a.reference_id,
            policy_result=a.policy_result,
            policy_reason=a.policy_reason,
            executed_at=a.executed_at,
            response_payload=a.response_payload
        )
        for a in c.recovery_actions
    ]
    
    audit_logs = [
        AuditLogResponse(
            id=log.id,
            actor=log.actor,
            event_name=log.event_name,
            reason=log.reason,
            log_metadata=log.log_metadata,
            created_at=log.created_at
        )
        for log in c.audit_logs
    ]
    
    pred = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.case_id == c.id)
        .order_by(ModelPrediction.created_at.desc())
        .first()
    )
    latest_pred_resp = ModelPredictionResponse.model_validate(pred) if pred else None

    return RecoveryCaseDetail(
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
        created_at=c.created_at,
        updated_at=c.updated_at,
        resolved_at=c.resolved_at,
        customer=customer_resp,
        event_type=event_type,
        failure_reason=failure_reason,
        actions=actions,
        audit_logs=audit_logs,
        latest_prediction=latest_pred_resp,
    )


@router.post("/{case_id}/evaluate", response_model=RecoveryCaseDetail)
def evaluate_case(
    case_id: str,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    from app.services.recovery_service import execute_case_pipeline
    c = db.query(RecoveryCase).filter(
        RecoveryCase.id == case_id,
        RecoveryCase.merchant_id == current_merchant.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    execute_case_pipeline(db, case_id)
    return get_recovery_case(case_id, current_merchant, db)


class ReviewRequest(BaseModel):
    reason: Optional[str] = None


@router.post("/{case_id}/approve", response_model=RecoveryCaseDetail)
def approve_escalated_case(
    case_id: str,
    req: Optional[ReviewRequest] = None,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    from app.services.recovery_service import handle_human_review
    c = db.query(RecoveryCase).filter(
        RecoveryCase.id == case_id,
        RecoveryCase.merchant_id == current_merchant.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    reason = req.reason if req else None
    handle_human_review(db, case_id, approved=True, reason=reason)
    return get_recovery_case(case_id, current_merchant, db)


@router.post("/{case_id}/reject", response_model=RecoveryCaseDetail)
def reject_escalated_case(
    case_id: str,
    req: Optional[ReviewRequest] = None,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    from app.services.recovery_service import handle_human_review
    c = db.query(RecoveryCase).filter(
        RecoveryCase.id == case_id,
        RecoveryCase.merchant_id == current_merchant.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    reason = req.reason if req else None
    handle_human_review(db, case_id, approved=False, reason=reason)
    return get_recovery_case(case_id, current_merchant, db)


@router.post("/{case_id}/execute", response_model=RecoveryCaseDetail)
def execute_case(
    case_id: str,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    from app.services.recovery_service import execute_approved_action
    c = db.query(RecoveryCase).filter(
        RecoveryCase.id == case_id,
        RecoveryCase.merchant_id == current_merchant.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    execute_approved_action(db, case_id)
    return get_recovery_case(case_id, current_merchant, db)
