import json
from app.models.recovery_case import RecoveryCase
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.recovery_action import RecoveryAction
from app.services.razorpay_service import compute_signature_for_test
from app.services.recovery_service import (
    create_case_for_event,
    analyze_case,
    evaluate_policy_for_case,
    execute_approved_action,
    handle_human_review,
)


def test_primary_8499_recovery_full_loop(client, db):
    """
    Primary Case (Track 03 Core Requirement):
    Customer Arjun Mehta encounters an ₹8,499 payment failure.
    Complete autonomous cycle:
    Failure -> Ingestion -> Risk Engine (0.87) -> AI Root Cause (BANK_TECHNICAL) ->
    Decision (CREATE_PAYMENT_LINK) -> Policy Check (ALLOW) -> Razorpay Payment Link ->
    Payment -> Verified Webhook -> RECOVERED.
    """
    merchant_id = "MER_DEMO_01"

    # 1. Customer & Event Setup
    customer = Customer(
        merchant_id=merchant_id,
        name="Arjun Mehta",
        email="arjun.mehta@example.com",
        phone="+919876543210",
        success_rate=0.85,
        customer_value="HIGH",
        opted_out=False,
    )
    db.add(customer)
    db.flush()

    event = RevenueEvent(
        merchant_id=merchant_id,
        customer_id=customer.id,
        event_type="PAYMENT_FAILED",
        amount_paise=849900,  # ₹8,499.00
        failure_reason="temporary_bank_failure",
        source="synthetic",
    )
    db.add(event)
    db.flush()

    # 2. Ingestion & Case Creation
    case = create_case_for_event(db, event)
    assert case.status == "NEW"
    assert case.amount_at_risk_paise == 849900

    # 3. AI Analysis & Risk Scoring
    case = analyze_case(db, case.id)
    assert case.status == "READY"
    assert case.recovery_probability >= 0.80
    assert "[BANK_TECHNICAL]" in case.root_cause
    assert case.recommended_action == "CREATE_PAYMENT_LINK"

    # 4. Policy Engine Check
    case, _ = evaluate_policy_for_case(db, case.id)
    assert case.status == "APPROVED"
    assert case.attempt_count == 0

    # 5. Razorpay Execution
    case, plink_resp = execute_approved_action(db, case.id)
    assert case.status == "WAITING_RESULT"
    assert case.attempt_count == 1
    assert "https://rzp.io/i/" in plink_resp["short_url"]
    plink_id = plink_resp["id"]

    # Verify action recorded as SUCCESS
    action = db.query(RecoveryAction).filter(RecoveryAction.case_id == case.id).first()
    assert action is not None
    assert action.status == "SUCCESS"
    assert action.razorpay_entity_id == plink_id

    # 6. Incoming Razorpay Webhook (payment_link.paid)
    event_id = f"evt_e2e_{case.id}"
    webhook_payload = {
        "entity": "event",
        "account_id": "acc_test",
        "event": "payment_link.paid",
        "event_id": event_id,
        "payload": {
            "payment_link": {
                "entity": {
                    "id": plink_id,
                    "amount": 849900,
                    "amount_paid": 849900,
                    "currency": "INR",
                    "status": "paid",
                    "notes": {"case_id": case.id, "merchant_id": merchant_id},
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_verified_8499",
                    "amount": 849900,
                    "currency": "INR",
                    "status": "captured",
                }
            }
        }
    }
    raw_body = json.dumps(webhook_payload).encode("utf-8")
    sig = compute_signature_for_test(raw_body)

    wh_res = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )
    assert wh_res.status_code == 200

    # 7. Verification of Terminal State
    db.refresh(case)
    assert case.status == "RECOVERED"
    assert case.amount_recovered_paise == 849900
    assert case.resolved_at is not None

    db.refresh(action)
    assert action.status == "SUCCESS"

    # Verify Audit Trail contains PAYMENT_RECOVERED from RAZORPAY_WEBHOOK
    audit_trail = [(l.actor, l.event_name) for l in case.audit_logs]
    assert ("RAZORPAY_WEBHOOK", "PAYMENT_RECOVERED") in audit_trail


def test_guardrail_opt_out_stop_rule(db):
    """
    Guardrail Stopping Rule 1: Customer Opt-Out
    Customer Priya Nair has explicitly opted out.
    Enforcement: Policy engine halts recovery and generates ZERO payment links.
    """
    merchant_id = "MER_DEMO_01"
    customer = Customer(
        merchant_id=merchant_id,
        name="Priya Nair",
        email="priya.nair@example.com",
        phone="+919876543211",
        success_rate=0.70,
        customer_value="LOW",
        opted_out=True,  # OPTED OUT
    )
    db.add(customer)
    db.flush()

    event = RevenueEvent(
        merchant_id=merchant_id,
        customer_id=customer.id,
        event_type="PAYMENT_FAILED",
        amount_paise=320000,
        failure_reason="insufficient_funds",
        source="synthetic",
    )
    db.add(event)
    db.flush()

    case = create_case_for_event(db, event)
    case = analyze_case(db, case.id)
    case, _ = evaluate_policy_for_case(db, case.id)

    from app.models.audit_log import AuditLog

    # Invariant: Must transition to BLOCKED
    assert case.status == "BLOCKED"

    # Invariant: Zero payment links created
    actions = db.query(RecoveryAction).filter(RecoveryAction.case_id == case.id).all()
    assert len(actions) == 0

    # Audit Trail verification
    policy_logs = db.query(AuditLog).filter(AuditLog.case_id == case.id, AuditLog.event_name == "POLICY_BLOCKED").all()
    assert len(policy_logs) > 0
    assert "CUSTOMER_OPTOUT" in policy_logs[0].reason


def test_guardrail_max_attempts_ceiling_rule(db):
    """
    Guardrail Stopping Rule 2: Maximum Attempt Ceiling
    Case already reached attempt_count = 2.
    Enforcement: Halts recovery and transitions to BLOCKED.
    """
    from app.models.audit_log import AuditLog

    merchant_id = "MER_DEMO_01"
    customer = Customer(
        merchant_id=merchant_id,
        name="Karan Verma",
        email="karan@example.com",
        phone="+919876543212",
        success_rate=0.80,
        customer_value="MEDIUM",
        opted_out=False,
    )
    db.add(customer)
    db.flush()

    event = RevenueEvent(
        merchant_id=merchant_id,
        customer_id=customer.id,
        event_type="PAYMENT_FAILED",
        amount_paise=250000,
        failure_reason="gateway_timeout",
        source="synthetic",
    )
    db.add(event)
    db.flush()

    case = create_case_for_event(db, event)
    case.attempt_count = 2  # Already exhausted max attempts
    db.flush()

    case = analyze_case(db, case.id)
    case, _ = evaluate_policy_for_case(db, case.id)

    assert case.status == "BLOCKED"
    policy_logs = db.query(AuditLog).filter(AuditLog.case_id == case.id, AuditLog.event_name == "POLICY_BLOCKED").all()
    assert len(policy_logs) > 0
    assert "MAX_ATTEMPTS_REACHED" in policy_logs[0].reason


def test_high_value_escalation_rule(db):
    """
    Guardrail Rule 3: High-Value Escalation Threshold
    Transaction amount: ₹45,000 (exceeds default ₹10,000 threshold).
    Enforcement: Automatically transitions to ESCALATED awaiting human approval.
    """
    merchant_id = "MER_DEMO_01"
    customer = Customer(
        merchant_id=merchant_id,
        name="Rajesh Sharma",
        email="rajesh@example.com",
        phone="+919876543213",
        success_rate=0.90,
        customer_value="HIGH",
        opted_out=False,
    )
    db.add(customer)
    db.flush()

    event = RevenueEvent(
        merchant_id=merchant_id,
        customer_id=customer.id,
        event_type="PAYMENT_FAILED",
        amount_paise=4500000,  # ₹45,000.00
        failure_reason="card_network_timeout",
        source="synthetic",
    )
    db.add(event)
    db.flush()

    case = create_case_for_event(db, event)
    case = analyze_case(db, case.id)
    case, _ = evaluate_policy_for_case(db, case.id)

    # Invariant: Halts in ESCALATED
    assert case.status == "ESCALATED"
    assert case.escalation_status == "PENDING_REVIEW"

    # Human operator reviews and approves
    case = handle_human_review(db, case.id, approved=True, reason="VIP customer verified by phone")
    assert case.status == "APPROVED"
    assert case.escalation_status == "APPROVED"
