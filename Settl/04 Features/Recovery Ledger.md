# Recovery Ledger

## Purpose

Be the source of truth for recovered revenue.

## Rule

A successful API response is not enough to mark recovery.

Only verified payment evidence can move a case to `RECOVERED`.

## Case state

```text
NEW
ANALYZING
READY
POLICY_CHECK
APPROVED
EXECUTING
WAITING_RESULT
RECOVERED
FAILED
STOPPED
ESCALATED
BLOCKED
```
