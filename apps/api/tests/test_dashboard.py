def test_get_dashboard_summary(client):
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    
    # Assert KPI fields
    assert "revenue_at_risk_paise" in data
    assert "eligible_revenue_paise" in data
    assert "revenue_recovered_paise" in data
    assert "recovery_rate" in data
    assert "guardrail_blocks_count" in data
    assert "human_escalations_count" in data
    assert "recent_cases" in data
    
    assert data["revenue_at_risk_paise"] > 0
    assert len(data["recent_cases"]) > 0


def test_list_recovery_cases(client):
    response = client.get("/api/v1/recovery-cases")
    assert response.status_code == 200
    cases = response.json()
    assert isinstance(cases, list)
    assert len(cases) >= 4

    # Check the primary seeded case
    case_8499 = next((c for c in cases if c["amount_at_risk_paise"] == 849900), None)
    assert case_8499 is not None
    assert case_8499["recommended_action"] in (
        "CREATE_PAYMENT_LINK", "SEND_REMINDER", "RECOVER_CHECKOUT",
        "MONITOR", "WAIT", "STOP", "RECORD_PROMISE", "CREATE_COLLECTION_CASE",
    )
    assert case_8499["status"] in ("READY", "APPROVED", "WAITING_RESULT", "RECOVERED", "BLOCKED", "ESCALATED")


def test_get_recovery_case_detail(client):
    response = client.get("/api/v1/recovery-cases/CASE_8499_RECOVERABLE")
    assert response.status_code == 200
    detail = response.json()
    assert detail["id"] == "CASE_8499_RECOVERABLE"
    assert detail["amount_at_risk_paise"] == 849900
    assert detail["customer"] is not None
    assert detail["customer"]["name"] == "Ananya Sharma"
    assert len(detail["audit_logs"]) >= 2
