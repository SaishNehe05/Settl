import requests

res = requests.post(
    "http://127.0.0.1:8000/api/v1/recovery-cases/manual",
    json={
        "customer_name": "Test",
        "amount_paise": 500000,
        "promise_date": "2026-09-10"
    },
    headers={"Authorization": "Bearer dummy_token"} # I need a real token or I can just test with test client
)
print(res.status_code)
print(res.text)
