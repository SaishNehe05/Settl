from app.models.recovery_case import RecoveryCase
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.services.razorpay_service import (
    create_recovery_payment_link,
    verify_razorpay_webhook_signature,
    compute_signature_for_test,
)


def test_payment_link_creation_paise(db):
    customer = Customer(
        merchant_id="MER_DEMO_01",
        name="Ananya Sharma",
        email="ananya@example.com",
        phone="+919876543210",
        success_rate=0.95,
        customer_value="HIGH",
        opted_out=False,
    )
    db.add(customer)
    db.flush()

    event = RevenueEvent(
        merchant_id="MER_DEMO_01",
        customer_id=customer.id,
        event_type="PAYMENT_FAILED",
        amount_paise=849900,
        failure_reason="temporary_bank_failure",
        source="synthetic",
    )
    db.add(event)
    db.flush()

    case = RecoveryCase(
        merchant_id="MER_DEMO_01",
        revenue_event_id=event.id,
        amount_at_risk_paise=849900,
        recovery_probability=0.88,
        priority="HIGH",
        attempt_count=0,
        status="APPROVED",
    )
    db.add(case)
    db.flush()

    res = create_recovery_payment_link(db, case, customer)
    assert res is not None
    assert "id" in res
    assert res["amount"] == 849900  # Strictly in paise
    assert "https://rzp.io/i/" in res["short_url"]
    assert res["notes"]["case_id"] == case.id
    assert res["notes"]["settl_managed"] == "true"


def test_payment_link_idempotency(db):
    from app.services.recovery_service import execute_approved_action
    customer = Customer(
        merchant_id="MER_DEMO_01",
        name="Vikram Patel",
        email="vikram@example.com",
        phone="+919876543211",
        success_rate=0.75,
        customer_value="MEDIUM",
        opted_out=False,
    )
    db.add(customer)
    db.flush()

    event = RevenueEvent(
        merchant_id="MER_DEMO_01",
        customer_id=customer.id,
        event_type="PAYMENT_FAILED",
        amount_paise=420000,
        failure_reason="gateway_timeout",
        source="synthetic",
    )
    db.add(event)
    db.flush()

    case = RecoveryCase(
        merchant_id="MER_DEMO_01",
        revenue_event_id=event.id,
        amount_at_risk_paise=420000,
        recovery_probability=0.80,
        priority="MEDIUM",
        attempt_count=0,
        status="APPROVED",
    )
    db.add(case)
    db.flush()

    # 1. Execute first time
    case, link1 = execute_approved_action(db, case.id)
    assert case.status == "WAITING_RESULT"
    first_link_id = link1["id"]

    # 2. Call create_recovery_payment_link again directly
    link2 = create_recovery_payment_link(db, case, customer)
    # Must return identical existing link with idempotent_hit
    assert link2["id"] == first_link_id
    assert link2.get("idempotent_hit") is True


def test_hmac_signature_verification():
    raw_payload = b'{"event":"payment_link.paid","account_id":"acc_123"}'
    test_secret = "my_super_secret_webhook_key"

    # Valid signature
    valid_sig = compute_signature_for_test(raw_payload, secret=test_secret)
    assert verify_razorpay_webhook_signature(raw_payload, valid_sig, secret=test_secret) is True

    # Tampered payload
    tampered_payload = b'{"event":"payment_link.paid","account_id":"acc_tampered"}'
    assert verify_razorpay_webhook_signature(tampered_payload, valid_sig, secret=test_secret) is False

    # Invalid signature string
    assert verify_razorpay_webhook_signature(raw_payload, "invalid_sig_123", secret=test_secret) is False
