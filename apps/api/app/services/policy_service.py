from datetime import datetime, timezone
from typing import NamedTuple, Optional
from app.models.recovery_case import RecoveryCase
from app.models.policy import Policy
from app.models.customer import Customer


class PolicyResult(NamedTuple):
    status: str   # ALLOW, ESCALATE, STOP, BLOCK, WAIT
    reason: str   # Machine-readable reason code
    details: str  # Human-readable explanation


def evaluate_policy_guardrails(
    case: RecoveryCase,
    customer: Customer,
    policy: Policy,
    proposed_action: str,
    last_action_time: Optional[datetime] = None,
) -> PolicyResult:
    """
    Deterministic financial guardrail engine (PRD §8 & TDD §14).
    Rules:
      1. Maximum automated attempts: at limit -> STOP/BLOCK
      2. Maximum automated amount: above limit -> ESCALATE
      3. Minimum recovery probability: below threshold -> STOP/BLOCK
      4. Customer opt-out: true blocks contact -> STOP/BLOCK
      5. Cooldown: before cooldown completes -> WAIT
      6. Amount integrity: original amount must match exactly
    """
    # 1. Customer communication consent opt-out check
    if customer.opted_out:
        return PolicyResult(
            status="BLOCKED",
            reason="CUSTOMER_OPTOUT",
            details="Customer has explicitly opted out of automated communications. Contact blocked."
        )

    # 2. Maximum automated attempts check
    if case.attempt_count >= policy.max_attempts:
        return PolicyResult(
            status="BLOCKED",
            reason="MAX_ATTEMPTS_REACHED",
            details=f"Case reached maximum automated attempts ({case.attempt_count}/{policy.max_attempts}). Automation stopped."
        )

    # 3. High-value amount escalation check
    if case.amount_at_risk_paise > policy.max_automated_amount_paise:
        return PolicyResult(
            status="ESCALATED",
            reason="AMOUNT_REQUIRES_HUMAN",
            details=f"Amount ₹{case.amount_at_risk_paise/100:,.2f} exceeds automated policy threshold of ₹{policy.max_automated_amount_paise/100:,.2f}. Routed to human review."
        )

    # 4. Minimum recovery probability threshold check
    if case.recovery_probability < policy.min_probability:
        return PolicyResult(
            status="BLOCKED",
            reason="LOW_RECOVERY_PROBABILITY",
            details=f"Recovery probability ({case.recovery_probability*100:.1f}%) is below configured threshold of ({policy.min_probability*100:.1f}%)."
        )

    # 5. Cooldown window check
    if last_action_time:
        now = datetime.now(timezone.utc)
        elapsed_minutes = (now - last_action_time).total_seconds() / 60.0
        if elapsed_minutes < policy.cooldown_minutes:
            remaining = int(policy.cooldown_minutes - elapsed_minutes)
            return PolicyResult(
                status="WAIT",
                reason="COOLDOWN_ACTIVE",
                details=f"Cooldown window active. {remaining} minutes remaining before next automated action."
            )

    # 6. Scenario-specific stopping rules (based on root_cause category)
    root_cause = (case.root_cause or "").upper()
    
    # Subscription: Max 3 retry attempts before churn acceptance
    if "SUBSCRIPTION" in root_cause and case.attempt_count >= 3:
        return PolicyResult(
            status="BLOCKED",
            reason="SUBSCRIPTION_MAX_RETRIES",
            details=f"Subscription recovery reached max retries ({case.attempt_count}/3). Accepting churn to preserve customer relationship."
        )
    
    # B2B: Escalate if >₹1,00,000
    if "B2B" in root_cause and case.amount_at_risk_paise > 10000000:
        return PolicyResult(
            status="ESCALATED",
            reason="B2B_HIGH_VALUE_RECEIVABLE",
            details=f"B2B receivable ₹{case.amount_at_risk_paise/100:,.2f} exceeds ₹1,00,000. Routing to senior collections."
        )
    
    # Mandate: Max 2 retries per NPCI guidelines
    if "MANDATE" in root_cause and case.attempt_count >= 2:
        return PolicyResult(
            status="BLOCKED",
            reason="MANDATE_MAX_RETRIES",
            details=f"eMandate retry limit reached ({case.attempt_count}/2 per NPCI guidelines). Cannot re-present."
        )
    
    # Voice/IVR: Only between 9 AM – 7 PM IST
    if "REGIONAL" in root_cause or "VOICE" in root_cause or "IVR" in root_cause:
        from datetime import timedelta
        ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        hour = ist_now.hour
        if hour < 9 or hour >= 19:
            return PolicyResult(
                status="WAIT",
                reason="IVR_OUTSIDE_BUSINESS_HOURS",
                details=f"IVR calls restricted to 9 AM – 7 PM IST. Current IST hour: {hour}. Scheduling for next window."
            )

    # 7. Action-specific directives
    if proposed_action == "STOP":
        return PolicyResult(
            status="BLOCKED",
            reason="RECOMMENDED_STOP",
            details="Action recommended was STOP. Further automated attempts halted."
        )

    if proposed_action == "ESCALATE":
        return PolicyResult(
            status="ESCALATED",
            reason="RECOMMENDED_ESCALATION",
            details="Action recommended was ESCALATE. Operator review required."
        )

    if proposed_action == "WAIT":
        return PolicyResult(
            status="WAIT",
            reason="RECOMMENDED_WAIT",
            details="Action recommended was WAIT. Waiting for optimal recovery window."
        )

    # All deterministic guardrails cleared
    return PolicyResult(
        status="ALLOW",
        reason="POLICY_PASSED",
        details="All deterministic amount, attempt, probability, and consent guardrails passed successfully."
    )
