# Database Design

## Core tables

- `merchants`
- `customers`
- `orders`
- `payments`
- `revenue_events`
- `recovery_cases`
- `recovery_actions`
- `policies`
- `audit_logs`
- `model_predictions`
- `notifications`
- `webhook_events`

## Money representation

Always store money in **paise as BIGINT**.

Example:

`₹8,499 = 849900`

Never use floating-point numbers for financial amounts.

## Recovery case

Important fields:

```text
id
revenue_event_id
amount_at_risk_paise
recovery_probability
root_cause
priority
recommended_action
actual_action
attempt_count
status
amount_recovered_paise
escalation_status
created_at
resolved_at
```

## Idempotency

Use unique constraints for:

- provider + external event ID
- active recovery action per case/action type
- unique recovery reference
