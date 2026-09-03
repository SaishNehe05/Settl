from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


class AuditLogResponse(BaseModel):
    id: str
    actor: str
    event_name: str
    reason: Optional[str] = None
    log_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecoveryActionResponse(BaseModel):
    id: str
    action_type: str
    status: str
    razorpay_entity_id: Optional[str] = None
    reference_id: Optional[str] = None
    policy_result: Optional[str] = None
    policy_reason: Optional[str] = None
    executed_at: datetime
    response_payload: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class CustomerResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    success_rate: float
    customer_value: str
    opted_out: bool

    model_config = {"from_attributes": True}


class RecoveryCaseListItem(BaseModel):
    id: str
    merchant_id: str
    revenue_event_id: str
    amount_at_risk_paise: int
    recovery_probability: float
    root_cause: Optional[str] = None
    priority: str
    recommended_action: Optional[str] = None
    actual_action: Optional[str] = None
    attempt_count: int
    status: str
    amount_recovered_paise: int
    escalation_status: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModelPredictionResponse(BaseModel):
    id: str
    case_id: str
    model_name: str
    model_version: str
    probability: float
    root_cause_prediction: Optional[str] = None
    recommended_action: Optional[str] = None
    reason: Optional[str] = None
    features_hash: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecoveryCaseDetail(BaseModel):
    id: str
    merchant_id: str
    revenue_event_id: str
    amount_at_risk_paise: int
    recovery_probability: float
    root_cause: Optional[str] = None
    priority: str
    recommended_action: Optional[str] = None
    actual_action: Optional[str] = None
    attempt_count: int
    status: str
    amount_recovered_paise: int
    escalation_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    
    # Payment link details (extracted from latest CREATE_PAYMENT_LINK action)
    payment_link_id: Optional[str] = None
    payment_link_url: Optional[str] = None
    notification_status: Optional[str] = None
    
    # Nested context
    customer: Optional[CustomerResponse] = None
    event_type: Optional[str] = None
    failure_reason: Optional[str] = None
    source: Optional[str] = None
    payment_id: Optional[str] = None
    actions: List[RecoveryActionResponse] = []
    audit_logs: List[AuditLogResponse] = []
    latest_prediction: Optional[ModelPredictionResponse] = None

    model_config = {"from_attributes": True}


class CaseActionRunRequest(BaseModel):
    override_action: Optional[str] = None
    notes: Optional[str] = None


class CaseDecisionRequest(BaseModel):
    reason: Optional[str] = None
