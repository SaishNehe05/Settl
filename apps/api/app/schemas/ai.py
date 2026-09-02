from typing import List, Literal, Optional
from pydantic import BaseModel, Field


FailureCategory = Literal[
    "BANK_TECHNICAL",
    "CUSTOMER_SESSION",
    "INSUFFICIENT_FUNDS",
    "AUTHENTICATION",
    "PAYMENT_METHOD",
    "FRAUD_RISK",
    "SUBSCRIPTION_CHURN",
    "B2B_OVERDUE",
    "MANDATE_BOUNCE",
    "REGIONAL_VOICE",
    "PROMISE_TO_PAY",
    "UNKNOWN",
]

AllowedRecoveryAction = Literal[
    "CREATE_PAYMENT_LINK",
    "SEND_PAYMENT_LINK",
    "SEND_REMINDER",
    "RETRY_MANDATE",
    "INITIATE_IVR",
    "TRACK_PROMISE",
    "WAIT",
    "CUSTOMER_ACTION_REQUIRED",
    "SEND_FOLLOW_UP",
    "CREATE_COLLECTION_CASE",
    "ESCALATE",
    "STOP",
]

CommunicationChannel = Literal["WHATSAPP", "SMS", "EMAIL", "IVR"]


class RootCauseAnalysisOutput(BaseModel):
    failure_category: FailureCategory = Field(
        description="Standardized technical classification of why the payment failed or was abandoned."
    )
    summary: str = Field(
        description="Concise, human-readable diagnostic sentence explaining the root cause."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score in the diagnostic root-cause explanation (0.0 to 1.0)."
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="List of specific data points from the transaction or customer history supporting this diagnosis."
    )
    customer_sentiment_risk: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        default="LOW",
        description="Estimated risk of customer frustration or churn from outreach."
    )


class RecoveryDecisionOutput(BaseModel):
    recommended_action: AllowedRecoveryAction = Field(
        description="The strictly bounded recovery action recommendation."
    )
    channel: CommunicationChannel = Field(
        default="WHATSAPP",
        description="Optimal communication channel for customer outreach."
    )
    delay_minutes: int = Field(
        default=0,
        ge=0,
        description="Recommended cooldown or delay window in minutes before sending outreach."
    )
    reasoning: str = Field(
        description="Brief operational rationale for why this specific action and channel were selected."
    )


class CombinedAIAnalysis(BaseModel):
    root_cause: RootCauseAnalysisOutput
    decision: RecoveryDecisionOutput
    model_name: str
    provider: str
    latency_ms: int
    validation_status: str  # VALID, FALLBACK_INVALID_SCHEMA, FALLBACK_UNSUPPORTED_ACTION, FALLBACK_OFFLINE
