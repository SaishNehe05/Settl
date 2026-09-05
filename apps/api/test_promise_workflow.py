import os
import asyncio
from datetime import datetime, timedelta, timezone
from app.database import SessionLocal
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.recovery_case import RecoveryCase
from app.models.promise import Promise
from app.models.notification import Notification
from app.services.promise_worker import _process_overdue_promises

def test_promise_workflow():
    db = SessionLocal()
    try:
        # Get a merchant
        merchant = db.query(Merchant).first()
        if not merchant:
            print("No merchant found")
            return
            
        # Get a customer
        customer = db.query(Customer).first()
        if not customer:
            print("No customer found")
            return

        print(f"Using customer: {customer.email}")

        # Create event
        event = RevenueEvent(
            merchant_id=merchant.id,
            customer_id=customer.id,
            event_type="INVOICE_OVERDUE",
            provider_state="failed",
            amount_paise=500000,
            failure_reason="B2B overdue",
            raw_payload={"currency": "INR"}
        )
        db.add(event)
        db.flush()

        # Create case
        case = RecoveryCase(
            merchant_id=merchant.id,
            revenue_event_id=event.id,
            amount_at_risk_paise=500000,
            recovery_probability=0.8,
            status="APPROVED",
            priority="HIGH",
            attempt_count=0
        )
        db.add(case)
        db.flush()
        
        print(f"Created case {case.id}")

        # Create PROMISED promise, due in the past
        past_date = datetime.now(timezone.utc) - timedelta(days=2)
        promise = Promise(
            merchant_id=merchant.id,
            case_id=case.id,
            customer_id=customer.id,
            promised_amount_paise=500000,
            promise_date=past_date,
            status="PROMISED"
        )
        db.add(promise)
        db.commit()
        
        print(f"Created past-due promise {promise.id}")

        # Run worker loop iteration manually
        _process_overdue_promises()

        # Check promise status
        db.refresh(promise)
        print(f"Promise status after worker: {promise.status}")
        
        # Check notifications
        notifs = db.query(Notification).filter(Notification.case_id == case.id).all()
        print(f"Found {len(notifs)} notifications")
        for n in notifs:
            print(f"- {n.message_type}: {n.status} (recipient: {n.recipient})")
            print(f"  Content snippet: {n.content[:50]}...")

    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_promise_workflow()
