from typing import List, Optional
from datetime import datetime, timezone
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
    ManualCaseRequest,
)
from app.schemas.promise import PromiseCreate, PromiseResponse
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
            
        ext_inv_id = None
        due_at = None
        days_od = None
        if c.invoice:
            ext_inv_id = c.invoice.external_invoice_id
            due_at = c.invoice.due_at
            if due_at:
                now = datetime.now(timezone.utc)
                d_at = due_at if due_at.tzinfo else due_at.replace(tzinfo=timezone.utc)
                if now > d_at:
                    days_od = (now - d_at).days
        elif c.revenue_event and c.revenue_event.raw_payload and "days_overdue" in c.revenue_event.raw_payload:
            days_od = c.revenue_event.raw_payload["days_overdue"]

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
                source=c.revenue_event.source if c.revenue_event else None,
                subscription_id=c.subscription_id,
                billing_cycle_id=c.billing_cycle_id,
                provider_state=c.provider_state,
                invoice_id=c.invoice_id,
                external_invoice_id=ext_inv_id,
                invoice_due_at=due_at,
                days_overdue=days_od,
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
    source = None
    
    if c.revenue_event:
        event_type = c.revenue_event.event_type
        failure_reason = c.revenue_event.failure_reason
        source = c.revenue_event.source
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

    # Extract payment link details from the latest CREATE_PAYMENT_LINK action
    plink_action = next(
        (a for a in c.recovery_actions
         if a.action_type == "CREATE_PAYMENT_LINK" and a.razorpay_entity_id),
        None
    )
    payment_link_id = plink_action.razorpay_entity_id if plink_action else None
    payment_link_url = None
    notification_status = None
    if plink_action and plink_action.response_payload:
        payment_link_url = plink_action.response_payload.get("short_url")
    if payment_link_id and not payment_link_url:
        payment_link_url = f"https://rzp.io/i/{payment_link_id}"

    # Get notification status for this case
    from app.models.notification import Notification
    latest_notif = (
        db.query(Notification)
        .filter(Notification.case_id == c.id)
        .order_by(Notification.created_at.desc())
        .first()
    )
    if latest_notif:
        notification_status = latest_notif.status

    # Extract payment_id from revenue event
    payment_id_val = None
    if c.revenue_event:
        payment_id_val = getattr(c.revenue_event, 'payment_id', None)

    ext_inv_id = None
    due_at = None
    days_od = None
    inv_amount_paise = None
    inv_paid_amount_paise = None
    if c.invoice:
        ext_inv_id = c.invoice.external_invoice_id
        due_at = c.invoice.due_at
        inv_amount_paise = c.invoice.amount_paise
        inv_paid_amount_paise = c.invoice.paid_amount_paise
        if due_at:
            now = datetime.now(timezone.utc)
            d_at = due_at if due_at.tzinfo else due_at.replace(tzinfo=timezone.utc)
            if now > d_at:
                days_od = (now - d_at).days
    elif c.revenue_event and c.revenue_event.raw_payload and "days_overdue" in c.revenue_event.raw_payload:
        days_od = c.revenue_event.raw_payload["days_overdue"]

    promises_resp = [
        PromiseResponse.model_validate(p)
        for p in getattr(c, 'promises', [])
    ]

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
        payment_link_id=payment_link_id,
        payment_link_url=payment_link_url,
        notification_status=notification_status,
        customer=customer_resp,
        event_type=event_type,
        failure_reason=failure_reason,
        source=source,
        payment_id=payment_id_val,
        subscription_id=c.subscription_id,
        billing_cycle_id=c.billing_cycle_id,
        provider_state=c.provider_state,
        invoice_id=c.invoice_id,
        external_invoice_id=ext_inv_id,
        invoice_due_at=due_at,
        days_overdue=days_od,
        invoice_amount_paise=inv_amount_paise,
        invoice_paid_amount_paise=inv_paid_amount_paise,
        actions=actions,
        audit_logs=audit_logs,
        promises=promises_resp,
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


class PromiseRequest(BaseModel):
    amount_paise: int
    promise_date: str

@router.post("/{case_id}/promise", response_model=RecoveryCaseDetail)
def record_promise(
    case_id: str,
    req: PromiseRequest,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    from datetime import datetime, timezone
    from dateutil.parser import parse
    from app.models.promise import Promise
    from app.services.audit_service import log_audit_event
    
    c = db.query(RecoveryCase).filter(
        RecoveryCase.id == case_id,
        RecoveryCase.merchant_id == current_merchant.id
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
        
    if not c.revenue_event or not c.revenue_event.customer_id:
        raise HTTPException(status_code=400, detail="Case has no associated customer")

    promise_dt = parse(req.promise_date)
    
    # Use trusted amount from the actual case, NOT the request
    trusted_amount_paise = c.invoice.amount_paise if c.invoice else c.amount_at_risk_paise
    
    promise = Promise(
        merchant_id=current_merchant.id,
        case_id=c.id,
        customer_id=c.revenue_event.customer_id,
        invoice_id=c.invoice_id,
        promised_amount_paise=trusted_amount_paise,
        promise_date=promise_dt,
        status="PROMISED"
    )
    db.add(promise)
    db.flush() # ensure promise.id is generated
    
    log_audit_event(
        db=db,
        merchant_id=current_merchant.id,
        case_id=c.id,
        actor="MERCHANT_OPERATOR",
        event_name="PROMISE_TO_PAY_CREATED",
        reason=f"Recorded customer promise to pay ₹{trusted_amount_paise/100:,.2f} by {promise_dt.strftime('%Y-%m-%d')}.",
        metadata={
            "promise_id": promise.id,
            "promised_amount_paise": trusted_amount_paise,
            "promise_date": promise_dt.isoformat()
        }
    )
    db.commit()
    
    return get_recovery_case(case_id, current_merchant, db)

@router.post("/manual", response_model=RecoveryCaseDetail)
def create_manual_case(
    request: ManualCaseRequest,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    from app.models.customer import Customer
    from app.models.revenue_event import RevenueEvent
    from app.models.promise import Promise
    from app.services.audit_service import log_audit_event
    
    # Try to find existing customer by email
    customer = None
    if request.customer_email:
        customer = db.query(Customer).filter_by(merchant_id=current_merchant.id, email=request.customer_email).first()
    
    if not customer:
        customer = Customer(
            merchant_id=current_merchant.id,
            name=request.customer_name,
            email=request.customer_email or "unknown@example.com",
            phone=request.customer_phone
        )
        db.add(customer)
        db.flush()

    # Create Revenue Event
    revenue_event = RevenueEvent(
        merchant_id=current_merchant.id,
        customer_id=customer.id,
        event_type="MANUAL_ENTRY",
        provider_state="failed",
        amount_paise=request.amount_paise,
        failure_reason=request.notes or "Manual offline promise",
        raw_payload={"notes": request.notes}
    )
    db.add(revenue_event)
    db.flush()

    # Create Recovery Case
    new_case = RecoveryCase(
        merchant_id=current_merchant.id,
        revenue_event_id=revenue_event.id,
        amount_at_risk_paise=request.amount_paise,
        status="WAITING_RESULT", # Directly to waiting since there's an active promise
        priority="HIGH",
        recovery_probability=0.8,
        root_cause="OFFLINE_AGREEMENT",
        recommended_action="WAIT",
        attempt_count=0
    )
    db.add(new_case)
    db.flush()

    # Create Promise
    promise_dt = datetime.fromisoformat(request.promise_date).replace(tzinfo=timezone.utc)
    promise = Promise(
        merchant_id=current_merchant.id,
        case_id=new_case.id,
        customer_id=customer.id,
        promised_amount_paise=request.amount_paise,
        promise_date=promise_dt,
        status="PROMISED"
    )
    db.add(promise)
    db.flush()

    # Audit Events
    log_audit_event(
        db=db,
        merchant_id=current_merchant.id,
        case_id=new_case.id,
        actor="MERCHANT_OPERATOR",
        event_name="MANUAL_CASE_CREATED",
        reason=f"Created manual case for offline promise of ₹{request.amount_paise/100:,.2f}.",
    )
    log_audit_event(
        db=db,
        merchant_id=current_merchant.id,
        case_id=new_case.id,
        actor="MERCHANT_OPERATOR",
        event_name="PROMISE_TO_PAY_CREATED",
        reason=f"Recorded customer promise to pay by {promise_dt.strftime('%Y-%m-%d')}.",
        metadata={"promise_id": promise.id, "promise_date": promise_dt.isoformat()}
    )

    db.commit()
    
    return get_recovery_case(new_case.id, current_merchant, db)
