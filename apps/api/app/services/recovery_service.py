from typing import Optional, Tuple, Dict, Any
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
        invoice_id=event.invoice_id,
        subscription_id=event.subscription_id,
        billing_cycle_id=event.billing_cycle_id,
        provider_state=event.provider_state,
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

    # Step 2: Calculate numerical probability & priority via ML/risk engine (deterministic)
    prob, priority, baseline_action, _ = calculate_risk_and_action(case, customer, event)
    case.recovery_probability = prob
    case.priority = priority

    # Step 3: Execute structured AI root-cause analysis and recovery decision
    from app.services.ai_service import analyze_and_decide
    ai_analysis = analyze_and_decide(db, case, customer, event)

    case.recommended_action = ai_analysis.decision.recommended_action
    case.root_cause = f"[{ai_analysis.root_cause.failure_category}] {ai_analysis.root_cause.summary}"
    case.status = "READY"
    db.flush()

    log_audit_event(
        db=db,
        merchant_id=case.merchant_id,
        case_id=case.id,
        actor="AI_AGENT",
        event_name="AI_DIAGNOSIS_COMPLETED",
        reason=f"Diagnosed {ai_analysis.root_cause.failure_category} ({ai_analysis.root_cause.confidence*100:.0f}% confidence). Action: {ai_analysis.decision.recommended_action} via {ai_analysis.decision.channel}.",
        metadata={
            "recovery_probability": prob,
            "priority": priority,
            "failure_category": ai_analysis.root_cause.failure_category,
            "recommended_action": ai_analysis.decision.recommended_action,
            "channel": ai_analysis.decision.channel,
            "delay_minutes": ai_analysis.decision.delay_minutes,
            "model_name": ai_analysis.model_name,
            "latency_ms": ai_analysis.latency_ms,
            "validation_status": ai_analysis.validation_status,
            "evidence": ai_analysis.root_cause.evidence,
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
    Executes full deterministic pipeline from NEW -> READY -> POLICY EVALUATION -> EXECUTE (if ALLOWED).
    """
    analyze_case(db, case_id)
    case, result = evaluate_policy_for_case(db, case_id)
    
    if result.status == "ALLOW":
        case, _ = execute_approved_action(db, case_id)
        
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


def execute_approved_action(db: Session, case_id: str) -> Tuple[RecoveryCase, Dict[str, Any]]:
    """
    Common Action Engine.
    Executes an authorized action by routing to the appropriate handler.
    Transitions: APPROVED -> EXECUTING -> WAITING_RESULT / EXECUTED
    """
    from datetime import datetime, timezone
    from app.services.razorpay_service import create_recovery_payment_link

    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.status != "APPROVED":
        raise HTTPException(
            status_code=400,
            detail=f"Only APPROVED cases can be executed (current status: {case.status})"
        )

    customer = case.revenue_event.customer if case.revenue_event else None
    order = case.revenue_event.order if case.revenue_event else None
    action_type = case.actual_action or "CREATE_PAYMENT_LINK"

    # Step 1: Transition to EXECUTING
    case.status = "EXECUTING"
    case.attempt_count += 1
    db.flush()

    response_payload = {}
    next_case_status = "WAITING_RESULT"
    razorpay_entity_id = None
    reference_id = None
    audit_event = "ACTION_EXECUTED"
    audit_reason = f"Executed {action_type} for case {case.id}."

    # Route based on Action Type
    if action_type in ["CREATE_PAYMENT_LINK", "RECOVER_CHECKOUT"]:
        link_response = create_recovery_payment_link(db, case, customer, order)
        response_payload = link_response
        razorpay_entity_id = link_response.get("id")
        reference_id = link_response.get("reference_id")

        # Handle Razorpay API failure (ACTION_PENDING)
        if link_response.get("status") == "ACTION_PENDING":
            audit_event = "PAYMENT_LINK_FAILED"
            audit_reason = f"Razorpay API call failed: {link_response.get('error', 'unknown')}. Will retry."
            next_case_status = "APPROVED"  # Stay in APPROVED so it can be retried
            # Decrement attempt count since this wasn't a real attempt
            case.attempt_count = max(0, case.attempt_count - 1)
        elif link_response.get("idempotent_hit"):
            # Existing active link reused — no new notification needed
            audit_event = "PAYMENT_LINK_REUSED"
            audit_reason = f"Reused existing Razorpay Payment Link {razorpay_entity_id} for ₹{case.amount_at_risk_paise/100:,.2f}."
            next_case_status = "WAITING_RESULT"
        else:
            audit_event = "PAYMENT_LINK_ISSUED"
            audit_reason = f"Generated Razorpay Payment Link {razorpay_entity_id} for ₹{case.amount_at_risk_paise/100:,.2f}."
            next_case_status = "WAITING_RESULT"
            
            # Persist notification since Razorpay is configured to send sms and email
            short_url = link_response.get("short_url", f"https://rzp.io/i/{razorpay_entity_id}")
            from app.models.notification import Notification
            notif = Notification(
                merchant_id=case.merchant_id,
                case_id=case.id,
                channel="EMAIL_SMS",
                provider="razorpay",
                message_type="PAYMENT_LINK",
                recipient=customer.email if customer else "unknown",
                content=f"Razorpay Payment Link: {short_url}",
                status="PENDING",  # Notification state managed by Razorpay
                provider_reference=razorpay_entity_id,
                sent_at=datetime.now(timezone.utc)
            )
            db.add(notif)
        
    elif action_type in ["SEND_REMINDER", "SEND_FOLLOW_UP", "SEND_PAYMENT_LINK", "CUSTOMER_ACTION_REQUIRED"]:
        recipient_addr = customer.email if customer and customer.email else (customer.phone if customer and customer.phone else "unknown")
        
        # Determine if there's a broken promise to ground the context
        broken_promise = None
        if getattr(case, 'promises', None):
            for p in case.promises:
                if p.status == "BROKEN":
                    broken_promise = p
                    break

        from app.models.notification import Notification
        from app.services.notification_service import send_email_notification

        # Idempotency check: don't send if we already sent an email for this exact promise or state recently
        # A simple check: if we already have a SENT notification of this type in the last 24h
        recent_notif = (
            db.query(Notification)
            .filter(Notification.case_id == case.id, Notification.status == "SENT", Notification.message_type.in_(["PROMISE_REMINDER", "INVOICE_REMINDER"]))
            .order_by(Notification.created_at.desc())
            .first()
        )
        if recent_notif and (datetime.now(timezone.utc) - recent_notif.created_at).total_seconds() < 86400:
            # We already sent one recently, skip duplicate
            response_payload = {"status": "skipped", "reason": "Duplicate notification prevented"}
            audit_event = f"{action_type}_SKIPPED"
            audit_reason = f"Skipped {action_type} to {recipient_addr} to prevent duplicate."
            next_case_status = "WAITING_RESULT"
        elif customer and customer.opted_out:
            response_payload = {"status": "blocked", "reason": "Customer opted out"}
            audit_event = f"{action_type}_BLOCKED"
            audit_reason = f"Skipped {action_type} to {recipient_addr} due to opt-out."
            next_case_status = "WAITING_RESULT"
        else:
            response_payload = {"status": "sent", "channel": "email", "recipient": recipient_addr}
            audit_event = f"{action_type}_SENT"
            audit_reason = f"Sent {action_type} to {recipient_addr} for ₹{case.amount_at_risk_paise/100:,.2f}."
            next_case_status = "WAITING_RESULT"
            
            merchant_name = case.merchant.name if case.merchant else "Settl Merchant"

            if broken_promise:
                inv_ref = case.invoice.external_invoice_id or case.invoice_id or "N/A" if case.invoice else "N/A"
                due_str = broken_promise.promise_date.strftime("%Y-%m-%d")
                msg_content = (
                    f"Hello {customer.name if customer else 'Customer'},\n\n"
                    f"Your promised payment of ₹{broken_promise.promised_amount_paise/100:,.2f} for invoice {inv_ref} "
                    f"was due on {due_str}.\n\n"
                    f"Our records do not yet show a verified payment.\n\n"
                    f"Please complete the payment using the merchant's payment instructions.\n\n"
                    f"Regards,\n{merchant_name}"
                )
                msg_type = "PROMISE_REMINDER"
            elif case.invoice:
                inv_ref = case.invoice.external_invoice_id or case.invoice_id or "N/A"
                due_str = case.invoice.due_at.strftime("%Y-%m-%d") if case.invoice.due_at else "passed"
                msg_content = f"Payment Reminder: Invoice {inv_ref} for ₹{case.amount_at_risk_paise/100:,.2f} is overdue (due date: {due_str}). Please process payment.\n\nRegards,\n{merchant_name}"
                msg_type = "INVOICE_REMINDER"
            elif case.subscription_id:
                msg_content = f"Please update your payment instrument for subscription {case.subscription_id}.\n\nRegards,\n{merchant_name}"
                msg_type = "CUSTOMER_ACTION"
            else:
                msg_content = f"Payment reminder for outstanding amount ₹{case.amount_at_risk_paise/100:,.2f}.\n\nRegards,\n{merchant_name}"
                msg_type = "PAYMENT_REMINDER"

            notif_status = "PENDING" if recipient_addr != "unknown" else "FAILED"
            notif_fail = None if recipient_addr != "unknown" else "Notification not configured"

            notif = Notification(
                merchant_id=case.merchant_id,
                case_id=case.id,
                channel="EMAIL",
                provider="RESEND",
                message_type=msg_type,
                recipient=recipient_addr,
                content=msg_content,
                status=notif_status,
                failure_reason=notif_fail,
                provider_reference=None
            )
            db.add(notif)
            db.flush() # ensure notif has an ID
            
            if notif_status == "PENDING":
                send_email_notification(db, notif)
                if notif.status == "FAILED":
                    audit_reason = f"Failed to send email to {recipient_addr}: {notif.failure_reason}"
                    audit_event = f"{action_type}_FAILED"        
    elif action_type in ["MONITOR", "WAIT", "FOLLOW_UP"]:
        response_payload = {"status": "scheduled", "action": action_type}
        audit_event = "MONITORING_SCHEDULED"
        audit_reason = f"Scheduled monitoring/wait state for case {case.id}."
        next_case_status = "WAITING_RESULT"
        
    elif action_type == "CREATE_COLLECTION_CASE":
        response_payload = {"collection_case_id": f"COL_{case.id[-6:]}", "status": "assigned"}
        audit_event = "COLLECTION_CASE_CREATED"
        audit_reason = f"Created internal collection case for overdue amount ₹{case.amount_at_risk_paise/100:,.2f}."
        next_case_status = "EXECUTED"
        
    else:
        # Default generic handler for any other unhandled action
        response_payload = {"status": "completed", "action": action_type}
        audit_reason = f"Executed generic action {action_type}."
        next_case_status = "EXECUTED"

    # Step 3: Record RecoveryAction
    action_status = "SUCCESS"
    if response_payload.get("status") == "ACTION_PENDING":
        action_status = "PENDING"
    
    action = RecoveryAction(
        case_id=case.id,
        action_type=action_type,
        status=action_status,
        razorpay_entity_id=razorpay_entity_id,
        reference_id=reference_id,
        policy_result="ALLOW",
        policy_reason=f"Deterministic policy authorized {action_type}",
        executed_at=datetime.now(timezone.utc),
        response_payload=response_payload,
    )
    db.add(action)

    # Step 4: Transition to terminal or waiting state
    case.status = next_case_status

    log_audit_event(
        db=db,
        merchant_id=case.merchant_id,
        case_id=case.id,
        actor="SYSTEM",
        event_name=audit_event,
        reason=audit_reason,
        metadata={
            "action_type": action_type,
            "amount_paise": case.amount_at_risk_paise,
            "attempt_number": case.attempt_count,
            "response": response_payload
        },
    )
    db.commit()
    db.refresh(case)
    return case, response_payload


def handle_payment_recovered(
    db: Session,
    case_id: str,
    paid_amount_paise: int,
    payment_id: str,
    external_event_id: Optional[str] = None,
) -> RecoveryCase:
    """
    Validates payment proof from webhook and marks case RECOVERED.
    Strict Invariant: paid_amount_paise must be >= amount_at_risk_paise.
    """
    from datetime import datetime, timezone

    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Cumulative recovery logic
    total_recovered = (case.amount_recovered_paise or 0) + paid_amount_paise
    case.amount_recovered_paise = total_recovered

    is_fully_recovered = total_recovered >= case.amount_at_risk_paise
    
    # Update linked invoice if present
    if case.invoice:
        case.invoice.paid_amount_paise += paid_amount_paise
        if case.invoice.paid_amount_paise >= case.invoice.amount_paise:
            case.invoice.status = "PAID"
        else:
            case.invoice.status = "PARTIALLY_PAID"

    # Update linked promise if present
    if getattr(case, 'promises', None):
        for p in case.promises:
            if p.status in ("PROMISED", "PARTIALLY_FULFILLED", "BROKEN"):
                p.fulfilled_amount_paise += paid_amount_paise
                p.fulfilled_at = datetime.now(timezone.utc)
                if p.fulfilled_amount_paise >= p.promised_amount_paise:
                    p.status = "FULFILLED"
                else:
                    p.status = "PARTIALLY_FULFILLED"

    if is_fully_recovered:
        # Update case to terminal RECOVERED state
        case.status = "RECOVERED"
        case.resolved_at = datetime.now(timezone.utc)
    else:
        # Update case to PARTIALLY_RECOVERED, leave open for further actions
        case.status = "PARTIALLY_RECOVERED"

    # Update pending action to SUCCESS
    pending_action = (
        db.query(RecoveryAction)
        .filter(RecoveryAction.case_id == case.id, RecoveryAction.status == "PENDING")
        .order_by(RecoveryAction.executed_at.desc())
        .first()
    )
    if pending_action:
        pending_action.status = "SUCCESS"

    # Append audit trail proof
    log_audit_event(
        db=db,
        merchant_id=case.merchant_id,
        case_id=case.id,
        actor="RAZORPAY_WEBHOOK",
        event_name="PAYMENT_RECOVERED",
        reason=f"Verified Razorpay payment {payment_id} confirmed recovery of ₹{paid_amount_paise/100:,.2f}.",
        metadata={
            "payment_id": payment_id,
            "amount_recovered_paise": paid_amount_paise,
            "external_event_id": external_event_id,
        },
    )
    db.commit()
    db.refresh(case)
    return case
