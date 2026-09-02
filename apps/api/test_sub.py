import json
import requests
from app.services.razorpay_service import compute_signature_for_test
from app.models.base import generate_uuid

# 1. Test subscription.pending
sub_id = "sub_test_123"
current_start = 1690000000

payload = {
    "event_id": generate_uuid("evt_sub"),
    "event": "subscription.pending",
    "payload": {
        "subscription": {
            "entity": {
                "id": sub_id,
                "status": "pending",
                "current_start": current_start,
                "notes": {
                    "expected_amount_paise": 99900,
                    "customer_email": "rahul@example.com"
                }
            }
        }
    }
}

raw_body = json.dumps(payload).encode("utf-8")
signature = compute_signature_for_test(raw_body)

res = requests.post(
    "http://localhost:8000/api/v1/webhooks/razorpay",
    data=raw_body,
    headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"}
)
print("Pending event:", res.status_code, res.json())

# 2. Test duplicate (should be ignored)
res_dup = requests.post(
    "http://localhost:8000/api/v1/webhooks/razorpay",
    data=raw_body,
    headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"}
)
print("Duplicate event:", res_dup.status_code, res_dup.json())

# 3. Test subscription.charged (success)
payload_charged = {
    "event_id": generate_uuid("evt_sub2"),
    "event": "subscription.charged",
    "payload": {
        "subscription": {
            "entity": {
                "id": sub_id,
                "status": "active",
                "current_start": current_start
            }
        },
        "payment": {
            "entity": {
                "id": "pay_test_456",
                "amount": 99900
            }
        }
    }
}

raw_body_charged = json.dumps(payload_charged).encode("utf-8")
signature_charged = compute_signature_for_test(raw_body_charged)

res_charged = requests.post(
    "http://localhost:8000/api/v1/webhooks/razorpay",
    data=raw_body_charged,
    headers={"X-Razorpay-Signature": signature_charged, "Content-Type": "application/json"}
)
print("Charged event:", res_charged.status_code, res_charged.json())
