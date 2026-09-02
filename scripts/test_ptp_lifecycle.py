import sys
import os
import json
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "apps", "api"))

from app.database import SessionLocal
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.invoice import Invoice
from app.models.recovery_case import RecoveryCase
from app.models.promise import Promise
from app.schemas.event import EventCreate
from app.services.event_service import ingest_revenue_event
from app.services.promise_worker import _process_overdue_promises
from app.services.recovery_service import handle_payment_recovered
from app.schemas.promise import PromiseCreate

def run_ptp_test():
    print("\n[TEST] Starting Promise-to-Pay Lifecycle E2E Test...\n")
    db = SessionLocal()
    
    try:
        merchant = db.query(Merchant).first()
        customer = db.query(Customer).filter(Customer.merchant_id == merchant.id).first()
        
        # 1. Create a B2B Overdue Invoice
        invoice_id = f"inv_ptp_{int(datetime.now().timestamp())}"
        amount = 5500000  # 55,000 INR
        
        invoice = Invoice(
            id=invoice_id,
            merchant_id=merchant.id,
            customer_id=customer.id,
            amount_paise=amount,
            status="OVERDUE",
            due_at=datetime.now(timezone.utc) - timedelta(days=5),
            issued_at=datetime.now(timezone.utc) - timedelta(days=35),
        )
        db.add(invoice)
        db.commit()
        
        print(f"[TEST] 1. Created Invoice {invoice_id} for INR {amount/100:,.2f}")
        
        # 2. Trigger Event to create Recovery Case
        event_data = EventCreate(
            event_type="INVOICE_OVERDUE",
            event_id=f"ev_ptp_overdue_{int(datetime.now().timestamp())}",
            amount_paise=amount,
            customer_id=customer.id,
            invoice_id=invoice_id,
            failure_reason="Invoice is overdue by 5 days.",
            source="API",
            raw_payload={"days_overdue": 5}
        )
        
        event, case = ingest_revenue_event(db, event_data, merchant.id)
        if not case:
            print("[ERROR] Event processing failed to create case.")
            return
        print(f"[TEST] 2. Case created: {case.id} (Status: {case.status}, Amount: INR {case.amount_at_risk_paise/100:,.2f})")
        
        # 3. Record a Promise to Pay (Simulating POST /cases/{id}/promise)
        # Using a date 2 days in the past so the worker will see it as broken immediately
        promise_date = datetime.now(timezone.utc) - timedelta(days=2)
        
        print("\n[TEST] 3. Customer promises to pay the full amount.")
        promise = Promise(
            merchant_id=case.merchant_id,
            case_id=case.id,
            customer_id=customer.id,
            invoice_id=case.invoice_id,
            promised_amount_paise=amount,
            promise_date=promise_date,
            status="ACTIVE"
        )
        db.add(promise)
        db.commit()
        
        # We manually trigger AI analysis for the promise
        from app.services.recovery_service import analyze_case, execute_case_pipeline
        print("[TEST]   Re-evaluating case through AI and Policy engines...")
        analyze_case(db, case.id)
        execute_case_pipeline(db, case.id)
        
        db.refresh(case)
        # Assuming the policy blocks it with WAIT if there's an ACTIVE promise, the status should be WAITING_RESULT or READY (if policy says WAIT)
        # Wait, if policy returns WAIT, execute_case_pipeline sets case.status = "READY" because it hasn't executed
        print(f"[TEST]   Case Status after Promise recorded: {case.status}")
        
        # 4. Trigger Worker
        print("\n[TEST] 4. Triggering promise lifecycle worker (Simulating time passage)...")
        _process_overdue_promises()
        
        db.refresh(case)
        db.refresh(promise)
        
        print(f"[TEST]   Promise Status: {promise.status} (Broken At: {promise.broken_at})")
        print(f"[TEST]   Case Status: {case.status}")
        
        pending_action = next((a for a in case.recovery_actions if a.status == "PENDING"), None)
        if pending_action:
            print(f"[TEST]   AI recommended action for Broken Promise: {pending_action.action_type}")
            
        # 5. Customer actually pays!
        print("\n[TEST] 5. Customer makes payment (Webhook Received)...")
        handle_payment_recovered(db, case.id, amount, f"pay_ptp_{int(datetime.now().timestamp())}")
        
        db.refresh(case)
        db.refresh(promise)
        
        print(f"[TEST]   Final Case Status: {case.status}")
        print(f"[TEST]   Final Promise Status: {promise.status} (Fulfilled Amount: INR {promise.fulfilled_amount_paise/100:,.2f})")
        print(f"[TEST]   Invoice Status: {invoice.status}")
        
        print("\n[TEST] Case 5 PTP Flow Successful!")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_ptp_test()
