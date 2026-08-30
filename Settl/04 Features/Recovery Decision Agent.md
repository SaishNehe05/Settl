# Recovery Decision Agent

## Allowed actions

- `CREATE_PAYMENT_LINK`
- `SEND_PAYMENT_LINK`
- `SEND_REMINDER`
- `WAIT`
- `ESCALATE`
- `STOP`

## Decision input

- event type
- amount
- probability
- root cause
- attempts
- customer status
- merchant policy

## Output

```json
{
  "action": "CREATE_PAYMENT_LINK",
  "reason": "High recovery probability and no previous automated recovery attempt.",
  "expected_value_paise": 739400
}
```

## Hard rule

The action must be validated against the allowed enum before policy evaluation.
