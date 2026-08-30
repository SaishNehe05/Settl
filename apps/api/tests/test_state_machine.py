from app.models.recovery_case import RecoveryCase
from app.models.revenue_event import RevenueEvent
from app.models.customer import Customer
from app.services.recovery_service import (
    create_case_for_event,
    analyze_case,
    evaluate_policy_for_case,
    handle_human_review,
)


def test_state_machine_lifecycle(db):
    merchant_id = "MER_DEMO_01"

    customer = Customer(
        merchant_id=merchant_id,
        name="Lifecycle User",
        email="lifecycle@example.com",
        success_rate=0.92,
        customer_value="HIGH",
        opted_out=False
    )
    db.add(customer)
    db.flush()

    event = RevenueEvent(
        merchant_id=merchant_id,
        customer_id=customer.id,
        event_type="PAYMENT_FAILED",
        amount_paise=849900,
        failure_reason="temporary_bank_failure",
        source="synthetic"
    )
    db.add(event)
    db.flush()

    # Step 1: create_case -> NEW
    case = create_case_for_event(db, event)
    assert case.status == "NEW"

    # Step 2: analyze_case -> READY
    case = analyze_case(db, case.id)
    assert case.status == "READY"
    assert case.recovery_probability >= 0.70
    assert case.recommended_action == "CREATE_PAYMENT_LINK"

    # Step 3: evaluate_policy -> APPROVED
    case, res = evaluate_policy_for_case(db, case.id)
    assert case.status == "APPROVED"
    assert res.status == "ALLOW"


def test_human_operator_review_flow(client, db):
    # Ingest high value event that escalates
    resp = client.post("/api/v1/events/simulate", json={"scenario": "high_value"})
    case_id = resp.json()["case"]["id"]
    assert resp.json()["case"]["status"] == "ESCALATED"

    # 1. Operator rejects
    reject_resp = client.post(f"/api/v1/recovery-cases/{case_id}/reject", json={"reason": "Suspected abuse"})
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "STOPPED"
    assert reject_resp.json()["escalation_status"] == "REJECTED"

    # Audit log should contain HUMAN_REJECTED
    audit_events = [log["event_name"] for log in reject_resp.json()["audit_logs"]]
    assert "HUMAN_REJECTED" in audit_events
