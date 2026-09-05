import sys
sys.path.insert(0, ".")
from app.database import SessionLocal
from app.models.audit_log import AuditLog

db = SessionLocal()
logs = db.query(AuditLog).filter(AuditLog.case_id == "CASE_6ee2baf5ac77").order_by(AuditLog.created_at).all()
print("Audit trail ({} entries):".format(len(logs)))
for log in logs:
    reason = (log.reason or "n/a")[:140]
    print("  [{}] {}: {}".format(log.actor, log.event_name, reason))
db.close()
