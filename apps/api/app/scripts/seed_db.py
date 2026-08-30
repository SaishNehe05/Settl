import sys
import os
from datetime import datetime, timezone, timedelta

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import SessionLocal, engine, Base
from app.models.merchant import Merchant
from app.models.policy import Policy
from app.models.customer import Customer
from app.models.order import Order
from app.models.payment import Payment
from app.models.revenue_event import RevenueEvent
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.audit_log import AuditLog
from app.services.auth_service import get_password_hash


def seed():
    # Make sure all tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("🌱 Seeding database for Settl...")
        
        # 1. Check or create demo merchant
        merchant = db.query(Merchant).filter(Merchant.email == "demo@settl.ai").first()
        if not merchant:
            merchant = Merchant(
                id="MER_DEMO_01",
                name="Acme Retail India",
                email="demo@settl.ai",
                password_hash=get_password_hash("settl123")
            )
            db.add(merchant)
            db.flush()
            print(f"  ✓ Created Merchant: {merchant.name} ({merchant.email})")

        # 2. Check or create policy
        policy = db.query(Policy).filter(Policy.merchant_id == merchant.id).first()
        if not policy:
            policy = Policy(
                id="POL_DEMO_01",
                merchant_id=merchant.id,
                max_attempts=2,
                max_automated_amount_paise=1000000,  # ₹10,000
                min_probability=0.40,
                cooldown_minutes=240,
                human_review_above_paise=1000000
            )
            db.add(policy)
            db.flush()
            print("  ✓ Created Merchant Guardrail Policy")

        # 3. Create sample customers
        customers = {
            "ananya": Customer(
                id="CUS_ANANYA_01",
                merchant_id=merchant.id,
                external_customer_id="EXT_CUS_001",
                name="Ananya Sharma",
                email="ananya.sharma@example.com",
                phone="+919876543210",
                success_rate=0.95,
                customer_value="HIGH",
                opted_out=False
            ),
            "vikram": Customer(
                id="CUS_VIKRAM_02",
                merchant_id=merchant.id,
                external_customer_id="EXT_CUS_002",
                name="Vikram Patel",
                email="vikram.patel@example.com",
                phone="+919811223344",
                success_rate=0.65,
                customer_value="MEDIUM",
                opted_out=False
            ),
            "rohan": Customer(
                id="CUS_ROHAN_03",
                merchant_id=merchant.id,
                external_customer_id="EXT_CUS_003",
                name="Rohan Verma",
                email="rohan.verma@example.com",
                phone="+919988776655",
                success_rate=0.20,
                customer_value="LOW",
                opted_out=False
            ),
            "priya": Customer(
                id="CUS_PRIYA_04",
                merchant_id=merchant.id,
                external_customer_id="EXT_CUS_004",
                name="Priya Nair",
                email="priya.nair@example.com",
                phone="+919765432100",
                success_rate=0.85,
                customer_value="HIGH",
                opted_out=True
            ),
        }

        for k, c in customers.items():
            existing = db.query(Customer).filter(Customer.id == c.id).first()
            if not existing:
                db.add(c)
        db.flush()
        print("  ✓ Created Seed Customers")

        # 4. Create primary demo case: ₹8,499 (Ready for Phase 5 live test loop)
        now = datetime.now(timezone.utc)
        
        # Order 1: ₹8,499
        order_8499 = db.query(Order).filter(Order.id == "ORD_DEMO_8499").first()
        if not order_8499:
            order_8499 = Order(
                id="ORD_DEMO_8499",
                merchant_id=merchant.id,
                customer_id=customers["ananya"].id,
                external_order_id="EXT_ORD_8499",
                amount_paise=849900,
                currency="INR",
                status="PAYMENT_FAILED",
                created_at=now - timedelta(minutes=25)
            )
            db.add(order_8499)
            db.flush()

            pay_8499 = Payment(
                id="PAY_DEMO_8499",
                order_id=order_8499.id,
                external_payment_id="pay_failed_8499",
                amount_paise=849900,
                status="FAILED",
                method="upi",
                failure_reason="temporary_bank_failure",
                created_at=now - timedelta(minutes=24)
            )
            db.add(pay_8499)

            evt_8499 = RevenueEvent(
                id="EVT_FAILED_8499",
                merchant_id=merchant.id,
                customer_id=customers["ananya"].id,
                order_id=order_8499.id,
                event_type="PAYMENT_FAILED",
                amount_paise=849900,
                failure_reason="temporary_bank_failure",
                source="synthetic",
                occurred_at=now - timedelta(minutes=24),
                raw_payload={
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Issuing bank network timeout during UPI authorization",
                    "source": "bank_gateway"
                }
            )
            db.add(evt_8499)
            db.flush()

            case_8499 = RecoveryCase(
                id="CASE_8499_RECOVERABLE",
                merchant_id=merchant.id,
                revenue_event_id=evt_8499.id,
                amount_at_risk_paise=849900,
                recovery_probability=0.87,
                root_cause="temporary_bank_failure",
                priority="HIGH",
                recommended_action="CREATE_PAYMENT_LINK",
                actual_action=None,
                attempt_count=0,
                status="READY",
                amount_recovered_paise=0,
                created_at=now - timedelta(minutes=23)
            )
            db.add(case_8499)
            db.flush()

            db.add(AuditLog(
                merchant_id=merchant.id,
                case_id=case_8499.id,
                actor="SYSTEM",
                event_name="EVENT_INGESTED",
                reason="Normalized PAYMENT_FAILED event of ₹8,499 for customer Ananya Sharma",
                metadata={"amount_paise": 849900, "source": "synthetic"},
                created_at=now - timedelta(minutes=23)
            ))
            db.add(AuditLog(
                merchant_id=merchant.id,
                case_id=case_8499.id,
                actor="AGENT",
                event_name="RISK_EVALUATED",
                reason="High recovery probability (87%) due to strong customer payment history (95% success rate)",
                metadata={"probability": 0.87, "recommended_action": "CREATE_PAYMENT_LINK"},
                created_at=now - timedelta(minutes=22)
            ))
            print("  ✓ Created Primary Seed Case: ₹8,499 (CASE_8499_RECOVERABLE)")

        # Case 2: Max attempts case (Policy stopping rule demonstration)
        case_stopped = db.query(RecoveryCase).filter(RecoveryCase.id == "CASE_MAX_ATTEMPTS").first()
        if not case_stopped:
            evt_stopped = RevenueEvent(
                id="EVT_MAX_ATTEMPTS",
                merchant_id=merchant.id,
                customer_id=customers["rohan"].id,
                event_type="PAYMENT_FAILED",
                amount_paise=450000,  # ₹4,500
                failure_reason="insufficient_funds",
                source="synthetic",
                occurred_at=now - timedelta(hours=5),
                raw_payload={"error_code": "INSUFFICIENT_FUNDS"}
            )
            db.add(evt_stopped)
            db.flush()

            case_stopped = RecoveryCase(
                id="CASE_MAX_ATTEMPTS",
                merchant_id=merchant.id,
                revenue_event_id=evt_stopped.id,
                amount_at_risk_paise=450000,
                recovery_probability=0.25,
                root_cause="insufficient_funds",
                priority="LOW",
                recommended_action="STOP",
                actual_action="STOP",
                attempt_count=2,
                status="BLOCKED",
                amount_recovered_paise=0,
                created_at=now - timedelta(hours=5)
            )
            db.add(case_stopped)
            db.flush()

            db.add(AuditLog(
                merchant_id=merchant.id,
                case_id=case_stopped.id,
                actor="POLICY_ENGINE",
                event_name="POLICY_BLOCKED",
                reason="Maximum automated attempts (2) reached. Action STOP enforced.",
                metadata={"max_attempts": 2, "attempt_count": 2},
                created_at=now - timedelta(hours=5)
            ))
            print("  ✓ Created Guardrail Demo Case: Max Attempts (CASE_MAX_ATTEMPTS)")

        # Case 3: High value case (Human Escalation demonstration)
        case_escalated = db.query(RecoveryCase).filter(RecoveryCase.id == "CASE_HIGH_VALUE").first()
        if not case_escalated:
            evt_escalated = RevenueEvent(
                id="EVT_HIGH_VALUE",
                merchant_id=merchant.id,
                customer_id=customers["vikram"].id,
                event_type="PAYMENT_FAILED",
                amount_paise=3500000,  # ₹35,000
                failure_reason="gateway_error",
                source="synthetic",
                occurred_at=now - timedelta(hours=1),
                raw_payload={"error_code": "GATEWAY_TIMEOUT"}
            )
            db.add(evt_escalated)
            db.flush()

            case_escalated = RecoveryCase(
                id="CASE_HIGH_VALUE",
                merchant_id=merchant.id,
                revenue_event_id=evt_escalated.id,
                amount_at_risk_paise=3500000,
                recovery_probability=0.72,
                root_cause="gateway_error",
                priority="URGENT",
                recommended_action="ESCALATE",
                actual_action=None,
                attempt_count=0,
                status="ESCALATED",
                amount_recovered_paise=0,
                escalation_status="PENDING_REVIEW",
                created_at=now - timedelta(hours=1)
            )
            db.add(case_escalated)
            db.flush()

            db.add(AuditLog(
                merchant_id=merchant.id,
                case_id=case_escalated.id,
                actor="POLICY_ENGINE",
                event_name="POLICY_ESCALATED",
                reason="Amount ₹35,000 exceeds automated threshold (₹10,000). Routed to human operator review queue.",
                metadata={"amount_paise": 3500000, "threshold_paise": 1000000},
                created_at=now - timedelta(hours=1)
            ))
            print("  ✓ Created High-Value Escalation Case: ₹35,000 (CASE_HIGH_VALUE)")

        # Case 4: Opted out customer case
        case_optout = db.query(RecoveryCase).filter(RecoveryCase.id == "CASE_OPTOUT").first()
        if not case_optout:
            evt_optout = RevenueEvent(
                id="EVT_OPTOUT",
                merchant_id=merchant.id,
                customer_id=customers["priya"].id,
                event_type="CHECKOUT_ABANDONED",
                amount_paise=620000,  # ₹6,200
                failure_reason="session_timeout",
                source="merchant_app",
                occurred_at=now - timedelta(minutes=45)
            )
            db.add(evt_optout)
            db.flush()

            case_optout = RecoveryCase(
                id="CASE_OPTOUT",
                merchant_id=merchant.id,
                revenue_event_id=evt_optout.id,
                amount_at_risk_paise=620000,
                recovery_probability=0.68,
                root_cause="session_timeout",
                priority="MEDIUM",
                recommended_action="STOP",
                actual_action="STOP",
                attempt_count=0,
                status="BLOCKED",
                amount_recovered_paise=0,
                created_at=now - timedelta(minutes=45)
            )
            db.add(case_optout)
            db.flush()

            db.add(AuditLog(
                merchant_id=merchant.id,
                case_id=case_optout.id,
                actor="POLICY_ENGINE",
                event_name="POLICY_BLOCKED",
                reason="Customer has opted out of automated recovery communications. Action blocked.",
                metadata={"customer_id": customers["priya"].id},
                created_at=now - timedelta(minutes=45)
            ))
            print("  ✓ Created Opt-Out Blocked Case (CASE_OPTOUT)")

        # Case 5: Verified Recovered case (Historic verified recovery)
        case_recovered = db.query(RecoveryCase).filter(RecoveryCase.id == "CASE_HISTORIC_RECOVERED").first()
        if not case_recovered:
            evt_recovered = RevenueEvent(
                id="EVT_HISTORIC_RECOVERED",
                merchant_id=merchant.id,
                customer_id=customers["ananya"].id,
                event_type="PAYMENT_FAILED",
                amount_paise=1250000,  # ₹12,500
                failure_reason="temporary_bank_failure",
                source="razorpay",
                occurred_at=now - timedelta(days=2)
            )
            db.add(evt_recovered)
            db.flush()

            case_recovered = RecoveryCase(
                id="CASE_HISTORIC_RECOVERED",
                merchant_id=merchant.id,
                revenue_event_id=evt_recovered.id,
                amount_at_risk_paise=1250000,
                recovery_probability=0.90,
                root_cause="temporary_bank_failure",
                priority="HIGH",
                recommended_action="CREATE_PAYMENT_LINK",
                actual_action="CREATE_PAYMENT_LINK",
                attempt_count=1,
                status="RECOVERED",
                amount_recovered_paise=1250000,
                created_at=now - timedelta(days=2),
                resolved_at=now - timedelta(days=2, hours=-2)
            )
            db.add(case_recovered)
            db.flush()

            db.add(RecoveryAction(
                case_id=case_recovered.id,
                action_type="CREATE_PAYMENT_LINK",
                status="SUCCESS",
                razorpay_entity_id="plink_demo_historic_01",
                reference_id="REC_EVT_HISTORIC_RECOVERED",
                policy_result="ALLOW",
                policy_reason="Passed amount and attempt guardrails",
                executed_at=now - timedelta(days=2, hours=-1)
            ))
            db.add(AuditLog(
                merchant_id=merchant.id,
                case_id=case_recovered.id,
                actor="RAZORPAY_WEBHOOK",
                event_name="RECOVERY_VERIFIED",
                reason="Verified payment_link.paid webhook received from Razorpay for exact amount ₹12,500.",
                metadata={"amount_paise": 1250000, "razorpay_payment_id": "pay_historic_success_01"},
                created_at=now - timedelta(days=2, hours=-2)
            ))
            print("  ✓ Created Historic Recovered Case: ₹12,500 (CASE_HISTORIC_RECOVERED)")

        db.commit()
        print("✅ Database seeding completed successfully!\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
