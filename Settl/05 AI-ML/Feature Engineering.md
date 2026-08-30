# Feature Engineering

## Candidate features

| Feature | Type |
|---|---|
| amount_paise | numeric |
| failure_reason | categorical |
| attempt_count | numeric |
| customer_success_rate | numeric |
| customer_value | categorical |
| minutes_since_event | numeric |
| previous_recovery_success_rate | numeric |
| opted_out | boolean |

## Rules

- Features must be reproducible.
- Feature generation must be versioned.
- Avoid leakage from future outcomes.
- Keep training and evaluation preprocessing identical.
