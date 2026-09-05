"""
Settl Case 3: Subscription Recovery E2E Test Script

This script creates a REAL Razorpay Test Mode subscription plan and subscription,
then simulates the subscription.pending and subscription.halted webhook events
that Razorpay would send when a subscription payment fails.

Usage:
    python scratch/test_subscription_e2e.py

Prerequisites:
    - pip install razorpay requests
    - RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env
    - API server running on localhost:8000
"""
import os
import sys
import json
import time
import hashlib
import hmac
import requests

# Load env
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
# scratch -> api -> apps -> Settl
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".env")
load_dotenv(env_path)

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "qwerty@settl")
API_BASE = os.getenv("API_URL", "http://127.0.0.1:8000")
MERCHANT_ID = "MER_DEMO_01"

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    print("❌ RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in .env")
    sys.exit(1)

print(f"🔑 Using Razorpay Key: {RAZORPAY_KEY_ID}")
print(f"🌐 API Base: {API_BASE}")
print()

# ─── Step 1: Create a Razorpay Plan (Test Mode) ─────────────────────────
print("=" * 60)
print("STEP 1: Creating Razorpay Test Mode Plan...")
print("=" * 60)

plan_payload = {
    "period": "monthly",
    "interval": 1,
    "item": {
        "name": "Settl Case 3 Test Plan",
        "amount": 49900,  # ₹499.00
        "currency": "INR",
        "description": "Test subscription plan for Case 3 E2E"
    },
    "notes": {
        "settl_merchant_id": MERCHANT_ID,
        "settl_test": "case_3_subscription"
    }
}

try:
    resp = requests.post(
        "https://api.razorpay.com/v1/plans",
        json=plan_payload,
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
        timeout=15,
    )
    resp.raise_for_status()
    plan = resp.json()
    plan_id = plan["id"]
    print(f"✅ Plan created: {plan_id}")
    print(f"   Name: {plan['item']['name']}")
    print(f"   Amount: ₹{plan['item']['amount']/100:.2f}")
    print()
except Exception as e:
    print(f"❌ Failed to create plan: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"   Response: {e.response.text}")
    sys.exit(1)

# ─── Step 2: Create a Razorpay Subscription (Test Mode) ──────────────────
print("=" * 60)
print("STEP 2: Creating Razorpay Test Mode Subscription...")
print("=" * 60)

sub_payload = {
    "plan_id": plan_id,
    "total_count": 6,
    "quantity": 1,
    "notes": {
        "settl_merchant_id": MERCHANT_ID,
        "settl_test": "case_3_subscription"
    },
    "notify_info": {
        "notify_phone": "9876543210",
        "notify_email": "testcase3@settl.dev"
    }
}

try:
    resp = requests.post(
        "https://api.razorpay.com/v1/subscriptions",
        json=sub_payload,
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
        timeout=15,
    )
    resp.raise_for_status()
    subscription = resp.json()
    sub_id = subscription["id"]
    sub_status = subscription.get("status", "created")
    print(f"✅ Subscription created: {sub_id}")
    print(f"   Status: {sub_status}")
    print(f"   Plan: {plan_id}")
    print(f"   Amount: ₹{plan['item']['amount']/100:.2f}/month")
    print()
except Exception as e:
    print(f"❌ Failed to create subscription: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"   Response: {e.response.text}")
    sys.exit(1)

# ─── Step 3: Simulate subscription.pending webhook ──────────────────────
print("=" * 60)
print("STEP 3: Simulating subscription.pending webhook...")
print("=" * 60)

current_start = int(time.time())
current_end = current_start + 30 * 24 * 60 * 60  # 30 days later

pending_webhook_payload = {
    "entity": "event",
    "account_id": "acc_test_settl",
    "event": "subscription.pending",
    "event_id": f"evt_sub_pending_{sub_id}_{int(time.time())}",
    "contains": ["subscription"],
    "payload": {
        "subscription": {
            "entity": {
                "id": sub_id,
                "entity": "subscription",
                "plan_id": plan_id,
                "status": "pending",
                "current_start": current_start,
                "current_end": current_end,
                "total_count": 6,
                "paid_count": 0,
                "remaining_count": 6,
                "short_url": f"https://rzp.io/i/{sub_id}",
                "charge_at": current_start,
                "notes": {
                    "settl_merchant_id": MERCHANT_ID,
                    "settl_test": "case_3_subscription"
                },
                "customer_notify": 1,
            }
        },
        "payment": {
            "entity": {
                "id": f"pay_test_sub_{int(time.time())}",
                "entity": "payment",
                "amount": 49900,
                "currency": "INR",
                "status": "failed",
                "method": "card",
                "email": "testcase3@settl.dev",
                "contact": "+919876543210",
                "notes": {
                    "settl_merchant_id": MERCHANT_ID,
                },
                "error_code": "BAD_REQUEST_ERROR",
                "error_description": "Subscription payment failed - card declined during auto-debit",
                "error_reason": "subscription_payment_declined",
            }
        }
    },
    "created_at": int(time.time()),
}

# Sign the webhook
webhook_body = json.dumps(pending_webhook_payload, separators=(",", ":"))
signature = hmac.new(
    RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
    webhook_body.encode("utf-8"),
    hashlib.sha256,
).hexdigest()

try:
    resp = requests.post(
        f"{API_BASE}/api/v1/webhooks/razorpay",
        data=webhook_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
        timeout=30,
    )
    print(f"   HTTP Status: {resp.status_code}")
    result = resp.json()
    print(f"   Response: {json.dumps(result, indent=2)}")
    
    if resp.status_code == 200:
        print(f"✅ subscription.pending webhook accepted!")
    else:
        print(f"⚠️  Unexpected status code: {resp.status_code}")
    print()
except Exception as e:
    print(f"❌ Failed to send webhook: {e}")
    sys.exit(1)

# ─── Step 4: Verify the recovery case was created ────────────────────────
print("=" * 60)
print("STEP 4: Verifying recovery case creation...")
print("=" * 60)

# Wait a moment for background processing
time.sleep(3)

try:
    # Get auth token first
    login_resp = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        json={"email": "admin@settl.dev", "password": "admin123"},
        timeout=10,
    )
    if login_resp.status_code == 200:
        token = login_resp.json().get("access_token", "")
    else:
        token = ""
        print(f"⚠️  Login failed ({login_resp.status_code}), trying without auth...")

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    cases_resp = requests.get(
        f"{API_BASE}/api/v1/recovery-cases",
        headers=headers,
        timeout=10,
    )
    
    if cases_resp.status_code == 200:
        cases = cases_resp.json()
        # Find our subscription case
        sub_cases = [c for c in cases if c.get("subscription_id") == sub_id]
        
        if sub_cases:
            case = sub_cases[0]
            print(f"✅ Recovery Case Found!")
            print(f"   Case ID:          {case['id']}")
            print(f"   Status:           {case['status']}")
            print(f"   Provider State:   {case.get('provider_state', 'N/A')}")
            print(f"   Subscription ID:  {case.get('subscription_id', 'N/A')}")
            print(f"   Billing Cycle:    {case.get('billing_cycle_id', 'N/A')}")
            print(f"   Amount at Risk:   ₹{case['amount_at_risk_paise']/100:.2f}")
            print(f"   Recommended:      {case.get('recommended_action', 'N/A')}")
            print(f"   Priority:         {case['priority']}")
            print()
            
            # Verify the AI correctly diagnosed it
            if case.get('recommended_action') == 'WAIT':
                print("✅ AI correctly recommended WAIT (Razorpay native retry pending)")
            elif case.get('recommended_action') == 'CUSTOMER_ACTION_REQUIRED':
                print("✅ AI correctly recommended CUSTOMER_ACTION_REQUIRED")
            else:
                print(f"ℹ️  AI recommended: {case.get('recommended_action')}")
            
            # Get full case detail
            detail_resp = requests.get(
                f"{API_BASE}/api/v1/recovery-cases/{case['id']}",
                headers=headers,
                timeout=10,
            )
            if detail_resp.status_code == 200:
                detail = detail_resp.json()
                print(f"\n   Root Cause:       {detail.get('root_cause', 'N/A')}")
                print(f"   Audit Logs:       {len(detail.get('audit_logs', []))} entries")
                for log in detail.get('audit_logs', []):
                    print(f"     → [{log['actor']}] {log['event_name']}: {log.get('reason', '')[:80]}")
        else:
            print(f"⚠️  No subscription case found for {sub_id}")
            print(f"   Total cases returned: {len(cases)}")
            if cases:
                print(f"   Latest case: {cases[0].get('id')} (status: {cases[0].get('status')})")
    else:
        print(f"❌ Failed to fetch cases: {cases_resp.status_code}")
        print(f"   Response: {cases_resp.text[:500]}")
except Exception as e:
    print(f"❌ Verification failed: {e}")

# ─── Step 5: Simulate subscription.halted webhook ──────────────────────
print()
print("=" * 60)
print("STEP 5: Simulating subscription.halted webhook...")
print("=" * 60)

halted_webhook_payload = {
    "entity": "event",
    "account_id": "acc_test_settl",
    "event": "subscription.halted",
    "event_id": f"evt_sub_halted_{sub_id}_{int(time.time())}",
    "contains": ["subscription"],
    "payload": {
        "subscription": {
            "entity": {
                "id": sub_id,
                "entity": "subscription",
                "plan_id": plan_id,
                "status": "halted",
                "current_start": current_start,
                "current_end": current_end,
                "total_count": 6,
                "paid_count": 0,
                "remaining_count": 6,
                "short_url": f"https://rzp.io/i/{sub_id}",
                "charge_at": current_start,
                "notes": {
                    "settl_merchant_id": MERCHANT_ID,
                    "settl_test": "case_3_subscription"
                },
                "customer_notify": 1,
            }
        },
        "payment": {
            "entity": {
                "id": f"pay_test_halted_{int(time.time())}",
                "entity": "payment",
                "amount": 49900,
                "currency": "INR",
                "status": "failed",
                "method": "card",
                "email": "testcase3@settl.dev",
                "contact": "+919876543210",
                "notes": {
                    "settl_merchant_id": MERCHANT_ID,
                },
                "error_code": "BAD_REQUEST_ERROR",
                "error_description": "Subscription halted - all retry attempts exhausted",
                "error_reason": "subscription_halted_retries_exhausted",
            }
        }
    },
    "created_at": int(time.time()),
}

# Sign the webhook
webhook_body_halted = json.dumps(halted_webhook_payload, separators=(",", ":"))
signature_halted = hmac.new(
    RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
    webhook_body_halted.encode("utf-8"),
    hashlib.sha256,
).hexdigest()

try:
    resp = requests.post(
        f"{API_BASE}/api/v1/webhooks/razorpay",
        data=webhook_body_halted,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature_halted,
        },
        timeout=30,
    )
    print(f"   HTTP Status: {resp.status_code}")
    result = resp.json()
    print(f"   Response: {json.dumps(result, indent=2)}")
    
    if resp.status_code == 200:
        print(f"✅ subscription.halted webhook accepted!")
    else:
        print(f"⚠️  Unexpected status code: {resp.status_code}")
    print()
except Exception as e:
    print(f"❌ Failed to send halted webhook: {e}")

# Wait and verify halted case
time.sleep(3)

try:
    cases_resp = requests.get(
        f"{API_BASE}/api/v1/recovery-cases",
        headers=headers,
        timeout=10,
    )
    if cases_resp.status_code == 200:
        cases = cases_resp.json()
        # The halted event should either update the existing case or create a new one
        # (since billing_cycle_id is same, it should be deduplicated and a new case won't be created)
        sub_cases = [c for c in cases if c.get("subscription_id") == sub_id]
        
        print(f"📊 Found {len(sub_cases)} subscription case(s) for {sub_id}")
        for sc in sub_cases:
            print(f"   → {sc['id']}: status={sc['status']}, provider_state={sc.get('provider_state', 'N/A')}, action={sc.get('recommended_action', 'N/A')}")
except Exception as e:
    print(f"⚠️  Verification check failed: {e}")

print()
print("=" * 60)
print("✅ Case 3 E2E Test Complete!")
print("=" * 60)
print()
print("Summary:")
print(f"  Razorpay Plan:         {plan_id}")
print(f"  Razorpay Subscription: {sub_id}")
print(f"  Webhook Endpoint:      {API_BASE}/api/v1/webhooks/razorpay")
print()
print("Next steps:")
print("  1. Open the Settl dashboard and navigate to the Recovery Queue")
print("  2. Verify the subscription case appears with the correct SUBSCRIPTION FAILED badge")
print("  3. Click into the case to see the full AI diagnosis and policy evaluation")
