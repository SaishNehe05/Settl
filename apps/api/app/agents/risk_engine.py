from typing import Dict, Any, Tuple
from app.models.recovery_case import RecoveryCase
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent

# Grounded base probabilities by standardized failure reason
FAILURE_REASON_BASE_PROBS: Dict[str, float] = {
    "temporary_bank_failure": 0.78,
    "network_timeout": 0.75,
    "gateway_timeout": 0.74,
    "gateway_error": 0.72,
    "bank_server_down": 0.70,
    "session_timeout": 0.65,
    "checkout_abandoned": 0.62,
    "authentication_failed": 0.52,
    "otp_expired": 0.50,
    "insufficient_funds": 0.25,
    "card_declined": 0.20,
    "card_expired": 0.15,
}


def calculate_risk_and_action(
    case: RecoveryCase,
    customer: Customer,
    event: RevenueEvent,
) -> Tuple[float, str, str, str]:
    """
    Deterministic baseline risk engine.
    Calculates:
      1. recovery_probability: Calibrated float [0.05, 0.95]
      2. priority: URGENT | HIGH | MEDIUM | LOW
      3. recommended_action: CREATE_PAYMENT_LINK | SEND_PAYMENT_LINK | SEND_REMINDER | WAIT | ESCALATE | STOP
      4. root_cause_summary: Grounded explanatory sentence
    """
    reason_key = (event.failure_reason or "").lower().strip()
    
    # 1. Base probability from failure reason
    base_prob = 0.45
    for key, prob in FAILURE_REASON_BASE_PROBS.items():
        if key in reason_key:
            base_prob = prob
            break

    # 2. Customer historical payment success rate modifier (-0.125 to +0.125)
    success_rate = customer.success_rate if customer.success_rate is not None else 0.5
    success_modifier = (success_rate - 0.5) * 0.25

    # 3. Customer value tier modifier
    val_tier = (customer.customer_value or "MEDIUM").upper()
    tier_modifier = 0.08 if val_tier == "HIGH" else (-0.08 if val_tier == "LOW" else 0.0)

    # 4. Attempt penalty (each previous attempt degrades expected recovery)
    attempt_penalty = case.attempt_count * 0.15

    # Aggregate calibrated probability
    raw_prob = base_prob + success_modifier + tier_modifier - attempt_penalty
    probability = round(max(0.05, min(0.95, raw_prob)), 4)

    # 5. Determine Priority
    amount = case.amount_at_risk_paise
    if amount >= 2500000 or (amount >= 1000000 and probability >= 0.75):
        priority = "URGENT"
    elif probability >= 0.70 or amount >= 500000:
        priority = "HIGH"
    elif probability >= 0.40:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    # 6. Select Recommended Action (Bounded Enum)
    if customer.opted_out:
        recommended_action = "STOP"
        root_cause_summary = f"Customer has explicitly opted out of recovery communications."
    elif case.attempt_count >= 2:
        recommended_action = "STOP"
        root_cause_summary = f"Maximum automated attempt limit reached ({case.attempt_count} attempts)."
    elif amount > 1000000:  # > ₹10,000
        recommended_action = "ESCALATE"
        root_cause_summary = (
            f"Amount of ₹{amount/100:,.2f} exceeds standard automated recovery limit of ₹10,000. "
            f"Requires human review."
        )
    elif probability < 0.40:
        recommended_action = "STOP"
        root_cause_summary = (
            f"Low recovery probability ({probability*100:.1f}%) due to '{event.failure_reason or 'unspecified error'}'."
        )
    else:
        recommended_action = "CREATE_PAYMENT_LINK"
        root_cause_summary = (
            f"Grounded in failure '{event.failure_reason or 'temporary failure'}' with "
            f"{customer.name}'s strong payment history ({success_rate*100:.0f}% success rate). "
            f"High recovery probability ({probability*100:.1f}%)."
        )

    return probability, priority, recommended_action, root_cause_summary
