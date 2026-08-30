from app.models.recovery_case import RecoveryCase
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.agents.risk_engine import calculate_risk_and_action


def test_risk_engine_clean_case():
    case = RecoveryCase(amount_at_risk_paise=849900, attempt_count=0)
    customer = Customer(name="Test User", success_rate=0.95, customer_value="HIGH", opted_out=False)
    event = RevenueEvent(failure_reason="temporary_bank_failure", amount_paise=849900)

    prob, priority, action, cause = calculate_risk_and_action(case, customer, event)
    assert prob >= 0.75
    assert priority in ["HIGH", "URGENT"]
    assert action == "CREATE_PAYMENT_LINK"
    assert "temporary" in cause.lower() or "strong" in cause.lower()


def test_risk_engine_high_value_case():
    case = RecoveryCase(amount_at_risk_paise=3500000, attempt_count=0)
    customer = Customer(name="VIP User", success_rate=0.90, customer_value="HIGH", opted_out=False)
    event = RevenueEvent(failure_reason="gateway_error", amount_paise=3500000)

    prob, priority, action, cause = calculate_risk_and_action(case, customer, event)
    assert priority == "URGENT"
    assert action == "ESCALATE"
    assert "human review" in cause.lower() or "exceeds" in cause.lower()


def test_risk_engine_opted_out_customer():
    case = RecoveryCase(amount_at_risk_paise=500000, attempt_count=0)
    customer = Customer(name="Opted Out", success_rate=0.80, customer_value="MEDIUM", opted_out=True)
    event = RevenueEvent(failure_reason="network_timeout", amount_paise=500000)

    prob, priority, action, cause = calculate_risk_and_action(case, customer, event)
    assert action == "STOP"
    assert "opted out" in cause.lower()


def test_risk_engine_max_attempts_reached():
    case = RecoveryCase(amount_at_risk_paise=500000, attempt_count=2)
    customer = Customer(name="Retry User", success_rate=0.70, customer_value="MEDIUM", opted_out=False)
    event = RevenueEvent(failure_reason="temporary_bank_failure", amount_paise=500000)

    prob, priority, action, cause = calculate_risk_and_action(case, customer, event)
    assert action == "STOP"
    assert "attempt limit" in cause.lower()
