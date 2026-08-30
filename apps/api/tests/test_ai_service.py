import pytest
from pydantic import ValidationError

from app.schemas.ai import (
    RootCauseAnalysisOutput,
    RecoveryDecisionOutput,
    AllowedRecoveryAction,
)
from app.models.recovery_case import RecoveryCase
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.model_prediction import ModelPrediction
from app.services.ai_service import analyze_and_decide
from app.services.recovery_service import analyze_case, create_case_for_event


def test_pydantic_schema_valid_outputs():
    rc = RootCauseAnalysisOutput(
        failure_category="BANK_TECHNICAL",
        summary="Server timeout at issuer switch.",
        confidence=0.92,
        evidence=["Gateway timeout code 504", "Customer has 90% historical success"],
        customer_sentiment_risk="LOW",
    )
    assert rc.failure_category == "BANK_TECHNICAL"
    assert len(rc.evidence) == 2

    dec = RecoveryDecisionOutput(
        recommended_action="CREATE_PAYMENT_LINK",
        channel="WHATSAPP",
        delay_minutes=0,
        reasoning="High intent customer; transient bank error.",
    )
    assert dec.recommended_action == "CREATE_PAYMENT_LINK"
    assert dec.channel == "WHATSAPP"


def test_pydantic_schema_rejects_unsupported_action():
    # LLM cannot invent actions outside the allowed enum
    with pytest.raises(ValidationError):
        RecoveryDecisionOutput(
            recommended_action="CHARGE_CARD_IMMEDIATELY",  # Unauthorized action
            channel="SMS",
            delay_minutes=0,
            reasoning="Attempting direct charge",
        )


def test_pydantic_schema_rejects_unsupported_category():
    with pytest.raises(ValidationError):
        RootCauseAnalysisOutput(
            failure_category="RANDOM_CATEGORY",  # Unauthorized category
            summary="Invalid",
            confidence=0.5,
        )


def test_ai_service_analyze_and_decide_persists_prediction(db):
    merchant_id = "MER_DEMO_01"
    customer = Customer(
        merchant_id=merchant_id,
        name="Sunita Rao",
        email="sunita@example.com",
        success_rate=0.88,
        customer_value="HIGH",
        opted_out=False,
    )
    db.add(customer)
    db.flush()

    event = RevenueEvent(
        merchant_id=merchant_id,
        customer_id=customer.id,
        event_type="PAYMENT_FAILED",
        amount_paise=849900,
        failure_reason="gateway_timeout",
        source="synthetic",
    )
    db.add(event)
    db.flush()

    case = create_case_for_event(db, event)

    # Run AI analysis
    ai_result = analyze_and_decide(db, case, customer, event)
    assert ai_result.root_cause.failure_category == "BANK_TECHNICAL"
    assert ai_result.decision.recommended_action == "CREATE_PAYMENT_LINK"
    assert ai_result.validation_status in ["VALID", "VALID_LOCAL_ENGINE"]

    # Verify record was stored in model_predictions table
    pred = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.case_id == case.id)
        .order_by(ModelPrediction.created_at.desc())
        .first()
    )
    assert pred is not None
    assert pred.model_name is not None
    assert "BANK_TECHNICAL" in pred.root_cause_prediction
    assert pred.recommended_action == "CREATE_PAYMENT_LINK"


def test_state_machine_with_ai_integration(db):
    merchant_id = "MER_DEMO_01"
    customer = Customer(
        merchant_id=merchant_id,
        name="Vikram Seth",
        email="vikram@example.com",
        success_rate=0.75,
        customer_value="MEDIUM",
        opted_out=False,
    )
    db.add(customer)
    db.flush()

    event = RevenueEvent(
        merchant_id=merchant_id,
        customer_id=customer.id,
        event_type="PAYMENT_FAILED",
        amount_paise=550000,
        failure_reason="session_timeout",
        source="synthetic",
    )
    db.add(event)
    db.flush()

    case = create_case_for_event(db, event)
    case = analyze_case(db, case.id)

    assert case.status == "READY"
    assert "[CUSTOMER_SESSION]" in case.root_cause
    assert case.recommended_action in ["CREATE_PAYMENT_LINK", "SEND_REMINDER"]

    # Verify audit log includes AI_DIAGNOSIS_COMPLETED
    audit_events = [log.event_name for log in case.audit_logs]
    assert "AI_DIAGNOSIS_COMPLETED" in audit_events
