from datetime import datetime, timezone, timedelta
from app.models.recovery_case import RecoveryCase
from app.models.customer import Customer
from app.models.policy import Policy
from app.services.policy_service import evaluate_policy_guardrails


def test_policy_allow_standard_case():
    policy = Policy(max_attempts=2, max_automated_amount_paise=1000000, min_probability=0.40, cooldown_minutes=240)
    customer = Customer(opted_out=False)
    case = RecoveryCase(attempt_count=0, amount_at_risk_paise=849900, recovery_probability=0.87)

    res = evaluate_policy_guardrails(case, customer, policy, "CREATE_PAYMENT_LINK")
    assert res.status == "ALLOW"
    assert res.reason == "POLICY_PASSED"


def test_policy_blocks_max_attempts():
    policy = Policy(max_attempts=2, max_automated_amount_paise=1000000, min_probability=0.40, cooldown_minutes=240)
    customer = Customer(opted_out=False)
    case = RecoveryCase(attempt_count=2, amount_at_risk_paise=849900, recovery_probability=0.87)

    res = evaluate_policy_guardrails(case, customer, policy, "CREATE_PAYMENT_LINK")
    assert res.status == "BLOCKED"
    assert res.reason == "MAX_ATTEMPTS_REACHED"


def test_policy_escalates_high_amount():
    policy = Policy(max_attempts=2, max_automated_amount_paise=1000000, min_probability=0.40, cooldown_minutes=240)
    customer = Customer(opted_out=False)
    case = RecoveryCase(attempt_count=0, amount_at_risk_paise=2500000, recovery_probability=0.80)

    res = evaluate_policy_guardrails(case, customer, policy, "CREATE_PAYMENT_LINK")
    assert res.status == "ESCALATED"
    assert res.reason == "AMOUNT_REQUIRES_HUMAN"


def test_policy_blocks_opt_out():
    policy = Policy(max_attempts=2, max_automated_amount_paise=1000000, min_probability=0.40, cooldown_minutes=240)
    customer = Customer(opted_out=True)
    case = RecoveryCase(attempt_count=0, amount_at_risk_paise=849900, recovery_probability=0.87)

    res = evaluate_policy_guardrails(case, customer, policy, "CREATE_PAYMENT_LINK")
    assert res.status == "BLOCKED"
    assert res.reason == "CUSTOMER_OPTOUT"


def test_policy_blocks_low_probability():
    policy = Policy(max_attempts=2, max_automated_amount_paise=1000000, min_probability=0.40, cooldown_minutes=240)
    customer = Customer(opted_out=False)
    case = RecoveryCase(attempt_count=0, amount_at_risk_paise=849900, recovery_probability=0.25)

    res = evaluate_policy_guardrails(case, customer, policy, "CREATE_PAYMENT_LINK")
    assert res.status == "BLOCKED"
    assert res.reason == "LOW_RECOVERY_PROBABILITY"


def test_policy_waits_during_cooldown():
    policy = Policy(max_attempts=2, max_automated_amount_paise=1000000, min_probability=0.40, cooldown_minutes=240)
    customer = Customer(opted_out=False)
    case = RecoveryCase(attempt_count=1, amount_at_risk_paise=849900, recovery_probability=0.85)

    # Action occurred 30 minutes ago (cooldown is 240 mins)
    recent_action = datetime.now(timezone.utc) - timedelta(minutes=30)
    res = evaluate_policy_guardrails(case, customer, policy, "CREATE_PAYMENT_LINK", last_action_time=recent_action)
    assert res.status == "WAIT"
    assert res.reason == "COOLDOWN_ACTIVE"
