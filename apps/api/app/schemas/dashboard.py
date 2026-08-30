from pydantic import BaseModel
from typing import List, Optional
from app.schemas.recovery_case import RecoveryCaseListItem


class DashboardSummary(BaseModel):
    revenue_at_risk_paise: int
    eligible_revenue_paise: int
    revenue_recovered_paise: int
    recovery_attempts_count: int
    recovery_rate: float
    guardrail_blocks_count: int
    human_escalations_count: int
    total_cases_count: int
    active_cases_count: int
    recovered_cases_count: int
    recent_cases: List[RecoveryCaseListItem] = []
