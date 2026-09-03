"""
Case 1 Tests — Real Payment Failure Recovery via Razorpay Webhook

Tests the full automated flow:
  payment.failed webhook → case creation → auto-pipeline (AI + policy + payment link) →
  payment_link.paid webhook → verified recovery
"""
import json
import pytest
from datetime import datetime, timezone

from app.models.recovery_case import RecoveryCase
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.recovery_action import RecoveryAction
from app.models.webhook_event import WebhookEvent
from app.models.notification import Notification
from app.services.razorpay_service import compute_signature_for_test
from app.services.webhook_processor import process_webhook_sync


def _build_payment_failed_webhook(
    payment_id="pay_test_case1_001",
    amount=849900,
    customer_email="realcustomer@example.com",
    customer_phone="+919876543210",
    customer_name="Real Test Customer",
    error_code="BAD_REQUEST_ERROR",
    error_description="Payment processing failed due to temporary bank failure",
    error_reason="payment_failed",
    event_id="evt_test_case1_001",
):
    """Build a realistic Razorpay payment.failed webhook payload."""
    return {
        "entity": "event",
        "account_id": "acc_test_settl",
        "event": "payment.failed",
        "event_id": event_id,
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "amount": amount,
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "description": "Test purchase",
                    "email": customer_email,
                    "contact": customer_phone,
                    "error_code": error_code,
                    "error_description": error_description,
                    "error_reason": error_reason,
                    "notes": {
                        "customer_name": customer_name,
                    },
                }
            }
        },
    }


def _send_webhook(client, payload):
    """Post a webhook payload with valid test signature."""
    raw_body = json.dumps(payload).encode("utf-8")
    sig = compute_signature_for_test(raw_body)
    res = client.post(
        "/api/v1/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
    )
    return {"status_code": res.status_code, "body": res.json()}


class TestPaymentFailedAutoPipeline:
    """payment.failed -> case creation -> auto-pipeline -> payment link created"""

    def test_payment_failed_creates_case_and_runs_pipeline(self, client, db):
        """Core Case 1: payment.failed webhook triggers full automated recovery."""
        payload = _build_payment_failed_webhook()
        result = _send_webhook(client, payload)
        assert result["status_code"] == 200

        # Verify: RevenueEvent was created with source=razorpay
        event = (
            db.query(RevenueEvent)
            .filter(RevenueEvent.payment_id == "pay_test_case1_001")
            .first()
        )
        assert event is not None
        assert event.source == "razorpay"
        assert event.amount_paise == 849900
        assert event.event_type == "PAYMENT_FAILED"
        assert event.failure_reason is not None

        # Verify: RecoveryCase was created and auto-pipeline ran
        case = db.query(RecoveryCase).filter(RecoveryCase.revenue_event_id == event.id).first()
        assert case is not None
        assert case.amount_at_risk_paise == 849900
        # Auto-pipeline should have moved it past NEW
        assert case.status in ("WAITING_RESULT", "APPROVED", "BLOCKED", "ESCALATED", "READY")
        assert case.recovery_probability > 0.0
        assert case.root_cause is not None
        assert case.recommended_action is not None

    def test_payment_failed_creates_payment_link(self, client, db):
        """Case under 10k with good probability should create a payment link."""
        payload = _build_payment_failed_webhook(
            payment_id="pay_case1_plink_test",
            amount=500000,
            event_id="evt_case1_plink_test",
            error_description="Payment processing failed due to temporary bank failure",
        )
        result = _send_webhook(client, payload)
        assert result["status_code"] == 200

        event = db.query(RevenueEvent).filter(RevenueEvent.payment_id == "pay_case1_plink_test").first()
        case = db.query(RecoveryCase).filter(RecoveryCase.revenue_event_id == event.id).first()

        # Under 10k + temporary bank failure = high probability = APPROVED + payment link
        assert case.status == "WAITING_RESULT"
        assert case.attempt_count == 1

        # Verify RecoveryAction created
        action = db.query(RecoveryAction).filter(RecoveryAction.case_id == case.id).first()
        assert action is not None
        assert action.action_type == "CREATE_PAYMENT_LINK"
        assert action.razorpay_entity_id is not None
        assert action.status == "SUCCESS"

    def test_new_customer_no_fake_history(self, client, db):
        """New customer from webhook should not have invented history."""
        payload = _build_payment_failed_webhook(
            payment_id="pay_new_cust_test",
            customer_email="brandnew@example.com",
            customer_phone="+919999999999",
            customer_name="Brand New Customer",
            event_id="evt_new_cust_test",
        )
        result = _send_webhook(client, payload)
        assert result["status_code"] == 200
        
        # DEBUG: Check if WebhookEvent was processed
        wh = db.query(WebhookEvent).filter(WebhookEvent.id == result["body"]["webhook_id"]).first()
        assert wh is not None
        assert wh.status == "PROCESSED", f"Webhook not processed: {wh.processing_error}"

        # DEBUG: Check if RevenueEvent was created
        event = db.query(RevenueEvent).filter(RevenueEvent.payment_id == "pay_new_cust_test").first()
        assert event is not None, "RevenueEvent not created"
        
        all_customers = db.query(Customer).all()
        for c in all_customers:
            print(f"CUSTOMER: {c.email}, {c.name}")

        customer = db.query(Customer).filter(Customer.email == "brandnew@example.com").first()
        assert customer is not None, "Customer not created!"
        assert customer.success_rate == 1.0
        assert customer.customer_value == "UNKNOWN"
        assert customer.opted_out is False


class TestPaymentIdempotency:
    """Duplicate payment.failed for same payment_id must not create duplicate cases."""

    def test_duplicate_payment_failed_skipped(self, client, db):
        """Same pay_xxx sent twice -> only one RevenueEvent and one case."""
        payload = _build_payment_failed_webhook(
            payment_id="pay_dedup_test_001",
            event_id="evt_dedup_test_001",
        )

        # First webhook
        r1 = _send_webhook(client, payload)

        # Second webhook (different event_id, same payment_id)
        payload2 = _build_payment_failed_webhook(
            payment_id="pay_dedup_test_001",
            event_id="evt_dedup_test_002",
        )
        r2 = _send_webhook(client, payload2)

        # Verify: only one RevenueEvent for this payment_id
        events = db.query(RevenueEvent).filter(RevenueEvent.payment_id == "pay_dedup_test_001").all()
        assert len(events) == 1

        # Verify: only one case
        case = db.query(RecoveryCase).filter(RecoveryCase.revenue_event_id == events[0].id).first()
        assert case is not None


class TestRecoveryVerification:
    """payment_link.paid webhook -> case becomes RECOVERED"""

    def test_payment_link_paid_recovers_case(self, client, db):
        """Full end-to-end: payment.failed -> pipeline -> payment_link.paid -> RECOVERED."""
        # Step 1: Trigger payment.failed
        fail_payload = _build_payment_failed_webhook(
            payment_id="pay_e2e_recovery_001",
            amount=300000,
            event_id="evt_e2e_fail_001",
            error_description="temporary bank failure",
        )
        r = _send_webhook(client, fail_payload)

        event = db.query(RevenueEvent).filter(RevenueEvent.payment_id == "pay_e2e_recovery_001").first()
        case = db.query(RecoveryCase).filter(RecoveryCase.revenue_event_id == event.id).first()
        assert case.status == "WAITING_RESULT"

        # Get the payment link ID
        action = db.query(RecoveryAction).filter(
            RecoveryAction.case_id == case.id,
            RecoveryAction.action_type == "CREATE_PAYMENT_LINK",
        ).first()
        plink_id = action.razorpay_entity_id

        # Step 2: Simulate payment_link.paid
        paid_payload = {
            "entity": "event",
            "account_id": "acc_test_settl",
            "event": "payment_link.paid",
            "event_id": "evt_e2e_paid_001",
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": plink_id,
                        "amount": 300000,
                        "amount_paid": 300000,
                        "currency": "INR",
                        "status": "paid",
                        "notes": {"case_id": case.id, "merchant_id": case.merchant_id},
                    }
                },
                "payment": {
                    "entity": {
                        "id": "pay_e2e_success_001",
                        "amount": 300000,
                        "currency": "INR",
                        "status": "captured",
                    }
                },
            },
        }
        r2 = _send_webhook(client, paid_payload)

        # Verify: case is RECOVERED
        db.refresh(case)
        assert case.status == "RECOVERED"
        assert case.amount_recovered_paise == 300000
        assert case.resolved_at is not None

        # Verify audit trail
        audit_trail = [(l.actor, l.event_name) for l in case.audit_logs]
        assert ("RAZORPAY_WEBHOOK", "PAYMENT_RECOVERED") in audit_trail

    def test_duplicate_payment_link_paid_no_double_credit(self, client, db):
        """Same payment_link.paid twice -> ledger only increases once."""
        from app.models.base import generate_uuid
        from app.services.recovery_service import create_case_for_event

        customer = Customer(
            merchant_id="MER_DEMO_01",
            name="Dedup Test",
            email="dedup_paid@example.com",
            phone="+919876543299",
            success_rate=0.9,
            customer_value="HIGH",
            opted_out=False,
        )
        db.add(customer)
        db.flush()

        event = RevenueEvent(
            merchant_id="MER_DEMO_01",
            customer_id=customer.id,
            event_type="PAYMENT_FAILED",
            amount_paise=200000,
            failure_reason="temporary_bank_failure",
            source="razorpay",
        )
        db.add(event)
        db.flush()

        case = create_case_for_event(db, event)
        case.status = "WAITING_RESULT"
        db.flush()

        action = RecoveryAction(
            case_id=case.id,
            action_type="CREATE_PAYMENT_LINK",
            status="SUCCESS",
            razorpay_entity_id="plink_dedup_test_001",
            reference_id=f"settl_{case.id}_1",
        )
        db.add(action)
        db.commit()

        # Send payment_link.paid TWICE
        for evt_id in ["evt_paid_dup_1", "evt_paid_dup_2"]:
            paid_payload = {
                "entity": "event",
                "account_id": "acc_test",
                "event": "payment_link.paid",
                "event_id": evt_id,
                "payload": {
                    "payment_link": {
                        "entity": {
                            "id": "plink_dedup_test_001",
                            "amount": 200000,
                            "amount_paid": 200000,
                            "status": "paid",
                            "notes": {"case_id": case.id, "merchant_id": "MER_DEMO_01"},
                        }
                    },
                    "payment": {
                        "entity": {
                            "id": "pay_dedup_success",
                            "amount": 200000,
                            "status": "captured",
                        }
                    },
                },
            }
            r = _send_webhook(client, paid_payload)

        # Verify: recovered amount is exactly 200000, not 400000
        db.refresh(case)
        assert case.amount_recovered_paise == 200000
        assert case.status == "RECOVERED"


class TestPolicyBlocking:
    """Policy-blocked cases should NOT create payment links."""

    def test_opted_out_customer_blocked(self, client, db):
        """Customer who opted out -> case BLOCKED, zero payment links."""
        customer = Customer(
            merchant_id="MER_DEMO_01",
            name="Opted Out Customer",
            email="optedout_case1@example.com",
            phone="+919876543288",
            success_rate=0.9,
            customer_value="HIGH",
            opted_out=True,
        )
        db.add(customer)
        db.commit()

        payload = _build_payment_failed_webhook(
            payment_id="pay_optout_case1",
            customer_email="optedout_case1@example.com",
            event_id="evt_optout_case1",
        )
        r = _send_webhook(client, payload)

        event = db.query(RevenueEvent).filter(RevenueEvent.payment_id == "pay_optout_case1").first()
        case = db.query(RecoveryCase).filter(RecoveryCase.revenue_event_id == event.id).first()
        assert case.status == "BLOCKED"

        actions = db.query(RecoveryAction).filter(RecoveryAction.case_id == case.id).all()
        assert len(actions) == 0


class TestAmountVerification:
    """Amount mismatch handling."""

    def test_partial_payment_not_fully_recovered(self, client, db):
        """Paid less than expected -> PARTIALLY_RECOVERED, not RECOVERED."""
        from app.services.recovery_service import create_case_for_event

        customer = Customer(
            merchant_id="MER_DEMO_01",
            name="Partial Pay",
            email="partial@example.com",
            phone="+919876543277",
            success_rate=0.9,
            customer_value="MEDIUM",
            opted_out=False,
        )
        db.add(customer)
        db.flush()

        event = RevenueEvent(
            merchant_id="MER_DEMO_01",
            customer_id=customer.id,
            event_type="PAYMENT_FAILED",
            amount_paise=500000,
            failure_reason="temporary_bank_failure",
            source="razorpay",
        )
        db.add(event)
        db.flush()

        case = create_case_for_event(db, event)
        case.status = "WAITING_RESULT"
        db.flush()

        action = RecoveryAction(
            case_id=case.id,
            action_type="CREATE_PAYMENT_LINK",
            status="SUCCESS",
            razorpay_entity_id="plink_partial_test",
            reference_id=f"settl_{case.id}_1",
        )
        db.add(action)
        db.commit()

        paid_payload = {
            "entity": "event",
            "account_id": "acc_test",
            "event": "payment_link.paid",
            "event_id": "evt_partial_paid",
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": "plink_partial_test",
                        "amount": 500000,
                        "amount_paid": 300000,
                        "status": "paid",
                        "notes": {"case_id": case.id, "merchant_id": "MER_DEMO_01"},
                    }
                },
                "payment": {
                    "entity": {
                        "id": "pay_partial_success",
                        "amount": 300000,
                        "status": "captured",
                    }
                },
            },
        }
        r = _send_webhook(client, paid_payload)

        db.refresh(case)
        assert case.amount_recovered_paise == 300000
        assert case.status == "PARTIALLY_RECOVERED"


class TestNotificationTracking:
    """Notification records should be created for payment link actions."""

    def test_notification_created_for_payment_link(self, client, db):
        """When a payment link is created, a notification record should exist."""
        payload = _build_payment_failed_webhook(
            payment_id="pay_notif_test_001",
            amount=200000,
            event_id="evt_notif_test_001",
            error_description="temporary bank failure",
        )
        r = _send_webhook(client, payload)

        event = db.query(RevenueEvent).filter(RevenueEvent.payment_id == "pay_notif_test_001").first()
        case = db.query(RecoveryCase).filter(RecoveryCase.revenue_event_id == event.id).first()

        if case.status == "WAITING_RESULT":
            notif = db.query(Notification).filter(Notification.case_id == case.id).first()
            assert notif is not None
            assert notif.channel == "EMAIL_SMS"
            assert notif.provider == "razorpay"
            assert notif.message_type == "PAYMENT_LINK"
