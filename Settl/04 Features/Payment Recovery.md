# Payment Recovery

## Primary workflow

```text
PAYMENT_FAILED
→ Revenue Event
→ Risk Score
→ Root Cause
→ Decision
→ Policy
→ CREATE_PAYMENT_LINK
→ Customer Payment
→ payment_link.paid
→ Verify
→ RECOVERED
```

## Example case

Amount: ₹8,499  
Previous attempts: 0  
Customer success history: strong  
Failure: temporary failure

Expected behavior:

- high recovery probability
- Payment Link recommendation
- policy approval
- one recovery link
- successful test payment
- verified recovery

## Failure case

Attempts already equal maximum.

Expected:

**STOP / ESCALATE**

No new financial action.
