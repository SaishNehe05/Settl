from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.recovery_case import RecoveryCase
from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer
from app.models.policy import Policy
from app.models.recovery_action import RecoveryAction
from app.agents.risk_engine import calculate_risk_and_action
from app.services.policy_service import evaluate_policy_guardrails, PolicyResult
from app.services.audit_service import log_audit_event


def create_case_for_event(db: Session, event: RevenueEvent) -> RecoveryCase:
    """
    Initializes a new recovery case in state NEW for an ingested revenue event.
    """
    existing_case = db.query(RecoveryCase).filter(RecoveryCase.revenue_event_id == event.id).first()
    if existing_case:
        return existing_case

    case = RecoveryCase(
        merchant_id=event.merchant_id,
        revenue_event_id=event.id,
        amount_at_risk_paise=event.amount_paise,
        recovery_probability=0.0,
        priority="MEDIUM",
        attempt_count=0,
        status="NEW",
        amount_recovered_paise=0,
    )
    db.add(case)
    db.flush()

    log_audit_event(
        db=db,
        merchant_id=case.merchant_id,
        case_id=case.id,
        actor="SYSTEM",
        event_name="CASE_CREATED",
        reason=f"Created recovery unit for event {event.id} ({event.event_type}) with amount ₹{event.amount_paise/100:,.2f}",
        metadata={"event_id": event.id, "amount_paise": event.amount_paise, "source": event.source},
    )
    db.commit()
    db.refresh(case)
    return case


def analyze_case(db: Session, case_id: str) -> RecoveryCase:
    """
    Executes risk scoring and root-cause analysis on a case.
    Transitions: NEW -> ANALYZING -> READY
    """
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    event = case.revenue_event
    customer = event.customer if event else None
    if not customer:
        customer = db.query(Customer).filter(Customer.id == event.customer_id).first() if event else None

    # Step 1: Transition to ANALYZING
    case.status = "ANALYZING"
    db.commit()

    # Step 2: Calculate grounded baseline probability & decision
    prob, priority, action, root_cause = calculate_risk_and_action(case, customer, event)

    case.recovery_probability = prob
    case.priority = priority
    case.recommended_action = action
    case.root_cause = root_cause
    case.status = "READY"
    db.flush()

    log_audit_event(
        db=db,
        merchant_id=case.merchant_id,
        case_id=case.id,
        actor="AGENT",
        event_name="RISK_ANALYZED",
        reason=f"Assessed {priority} priority, recovery probability {prob*100:.1f}%. Candidate action: {action}.",
        metadata={
            "recovery_probability": prob,
            "priority": priority,
            "recommended_action": action,
            "root_cause": root_cause,
        },
    )
    db.commit()
    db.refresh(case)
    return case


def evaluate_policy_for_case(db: Session, case_id: str) -> Tuple[RecoveryCase, PolicyResult]:
    """
    Evaluates policy guardrails against the recommended action.
    Transitions: READY -> POLICY_CHECK -> (APPROVED | BLOCKED | ESCALATED | READY)
    """
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    policy = db.query(Policy).filter(Policy.merchant_id == case.merchant_id).first()
    if not policy:
        policy = Policy(merchant_id=case.merchant_id)
        db.add(policy)
        db.flush()

    customer = case.revenue_event.customer if case.revenue_event else None

    # Check last action time for cooldown
    last_action = (
        db.query(RecoveryAction)
        .filter(RecoveryAction.case_id == case.id)
        .order_by(RecoveryAction.executed_at.desc())
        .first()
    )
    last_action_time = last_action.executed_at if last_action else None

    # Transition to POLICY_CHECK
    case.status = "POLICY_CHECK"
    db.flush()

    # Deterministic guardrail evaluation
    result = evaluate_policy_guardrails(
        case=case,
        customer=customer,
        policy=policy,
        proposed_action=case.recommended_action or "CREATE_PAYMENT_LINK",
        last_action_time=last_action_time,
    )

    if result.status == "ALLOW":
        case.status = "APPROVED"
        case.actual_action = case.recommended_action
    elif result.status == "ESCALATED":
        case.status = "ESCALATED"
        case.escalation_status = "PENDING_REVIEW"
        case.actual_action = "ESCALATE"
    elif result.status in ["BLOCKED", "STOP"]:
        case.status = "BLOCKED"
        case.actual_action = "STOP"
    elif result.status == "WAIT":
        case.status = "READY"
        case.actual_action = "WAIT"

    log_audit_event(
        db=db,
        merchant_id=case.merchant_id,
        case_id=case.id,
        actor="POLICY_ENGINE",
        event_name=f"POLICY_{result.status}",
        reason=f"Guardrail check result: {result.status} ({result.reason}). {result.details}",
        metadata={"policy_status": result.status, "reason_code": result.reason, "rule_details": result.details},
    )
    db.commit()
    db.refresh(case)
    return case, result


def execute_case_pipeline(db: Session, case_id: str) -> RecoveryCase:
    """
    Executes full deterministic pipeline from NEW -> READY -> POLICY EVALUATION.
    """
    analyze_case(db, case_id)
    case, _ = evaluate_policy_for_case(db, case_id)
    return case


def handle_human_review(db: Session, case_id: str, approved: bool, reason: Optional[str] = None) -> RecoveryCase:
    """
    Processes human review decision for an ESCALATED recovery case.
    """
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.status != "ESCALATED":
        raise HTTPException(status_code=400, detail=f"Case is not in ESCALATED state (current: {case.status})")

    if approved:
        case.status = "APPROVED"
        case.escalation_status = "APPROVED"
        case.actual_action = case.recommended_action or "CREATE_PAYMENT_LINK"
        log_event = "HUMAN_APPROVED"
        log_reason = reason or "Operator approved case for automated payment link creation."
    else:
        case.status = "STOPPED"
        case.escalation_status = "REJECTED"
        case.actual_action = "STOP"
        log_event = "HUMAN_REJECTED"
        log_reason = reason or "Operator rejected recovery attempt. Case terminated."

    log_audit_event(
        db=db,
        merchant_id=case.merchant_id,
        case_id=case.id,
        actor="HUMAN_OPERATOR",
        event_name=log_event,
        reason=log_reason,
        metadata={"decision": "APPROVED" if approved else "REJECTED", "operator_note": reason},
    )
    db.commit()
    db.refresh(case)
    return case
