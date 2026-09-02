def test_ingest_event_api(client):
    payload = {
        "event_id": "EVT_TEST_INGEST_01",
        "customer_name": "Siddharth Malhotra",
        "customer_email": "sid@example.com",
        "event_type": "PAYMENT_FAILED",
        "amount_paise": 649900,
        "failure_reason": "temporary_bank_failure",
        "source": "synthetic"
    }
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "event" in data
    assert "case" in data
    assert data["event"]["id"] == "EVT_TEST_INGEST_01"
    assert data["event"]["amount_paise"] == 649900
    assert data["case"]["status"] == "WAITING_RESULT"  # Passes policy and automatically executes


def test_ingest_event_idempotency(client):
    payload = {
        "event_id": "EVT_TEST_IDEMPOTENT_01",
        "customer_name": "Pooja Hegde",
        "customer_email": "pooja@example.com",
        "event_type": "PAYMENT_FAILED",
        "amount_paise": 150000,
        "failure_reason": "session_timeout",
        "source": "synthetic"
    }
    # First ingestion
    resp1 = client.post("/api/v1/events", json=payload)
    assert resp1.status_code == 201
    case1_id = resp1.json()["case"]["id"]

    # Duplicate ingestion with same event_id
    resp2 = client.post("/api/v1/events", json=payload)
    assert resp2.status_code == 201
    case2_id = resp2.json()["case"]["id"]

    # Same case returned without duplicate creation
    assert case1_id == case2_id



