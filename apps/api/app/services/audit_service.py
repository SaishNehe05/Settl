from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_audit_event(
    db: Session,
    merchant_id: str,
    case_id: str,
    actor: str,
    event_name: str,
    reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Creates an append-only, tamper-evident audit log record for a recovery case.
    Actors: SYSTEM, AGENT, POLICY_ENGINE, HUMAN_OPERATOR, RAZORPAY_WEBHOOK
    """
    audit = AuditLog(
        merchant_id=merchant_id,
        case_id=case_id,
        actor=actor,
        event_name=event_name,
        reason=reason,
        log_metadata=metadata,
    )
    db.add(audit)
    db.flush()
    return audit
