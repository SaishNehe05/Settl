import json
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.services.razorpay_service import compute_signature_for_test
from app.services.recovery_service import create_case_for_event, execute_case_pipeline, execute_approved_action


def test_webhook_missing_signature(client):
    res = client.post("/api/v1/webhooks/razorpay", content=b'{"event":"test"}')
    assert res.status_code == 400
    assert "Missing X-Razorpay-Signature" in res.json()["detail"]


def test_webhook_invalid_signature(client):
    res = client.post(
        "/api/v1/webhooks/razorpay",
        content=b'{"event":"test"}',
        headers={"X-Razorpay-Signature": "invalid_signature_xyz"}
    )
    assert res.status_code == 400
    assert "Invalid webhook signature" in res.json()["detail"]


def test_webhook_payment_link_paid_end_to_end(client, db):
    merchant_id = "MER_DEMO_01"
    customer = Customer(
        merchant_id=merchant_id,
        name="Webhook Tester",
        email="webhook.tester@example.com",
        phone="+919876543299",
        success_rate=0.95,
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

    # 1. Pipeline: NEW -> READY -> APPROVED -> WAITING_RESULT (Automatic Execution)
    case = create_case_for_event(db, event)
    case = execute_case_pipeline(db, case.id)
    assert case.status == "WAITING_RESULT"

    # We don't need to manually execute since it was automatic
    # Find the link generated automatically
    action = db.query(RecoveryAction).filter(RecoveryAction.case_id == case.id).first()
    plink_id = action.razorpay_entity_id

    # 3. Simulate incoming Razorpay payment_link.paid webhook
    event_id = f"evt_test_{case.id}"
    webhook_payload = {
        "entity": "event",
        "account_id": "acc_test",
        "event": "payment_link.paid",
        "event_id": event_id,
        "contains": ["payment_link", "payment"],
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
                    "id": "pay_verified_123",
                    "amount": 849900,
                    "currency": "INR",
                    "status": "captured",
                }
            }
        }
    }

    raw_body = json.dumps(webhook_payload).encode("utf-8")
    sig = compute_signature_for_test(raw_body)

    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 4. Verify case is RECOVERED with verified amount
    db.refresh(case)
    assert case.status == "RECOVERED"
    assert case.amount_recovered_paise == 849900
    assert case.resolved_at is not None

    # Verify audit log includes PAYMENT_RECOVERED from RAZORPAY_WEBHOOK
    audit_events = [(log.actor, log.event_name) for log in case.audit_logs]
    assert ("RAZORPAY_WEBHOOK", "PAYMENT_RECOVERED") in audit_events


def test_simulate_webhook_endpoint(client, db):
    # Test simulation endpoint
    resp = client.post("/api/v1/events/simulate", json={"scenario": "clean_recovery"})
    case_id = resp.json()["case"]["id"]

    # Since auto_pipeline=True, the case is already executed to WAITING_RESULT
    
    # 2. Simulate Webhook
    wh_resp = client.post(
        "/api/v1/webhooks/razorpay/simulate",
        json={"case_id": case_id}
    )
    assert wh_resp.status_code == 200
    assert wh_resp.json()["case_status"] == "RECOVERED"
    assert wh_resp.json()["amount_recovered_paise"] == 849900
