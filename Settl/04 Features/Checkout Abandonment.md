# Checkout Abandonment

## Scope

P1 — build after failed-payment recovery is complete.

## Detection

Our application records:

- CHECKOUT_STARTED
- PAYMENT_ATTEMPTED
- PAYMENT_SUCCESS

A scheduled process marks:

`CHECKOUT_ABANDONED`

when the configured timeout passes without successful payment.

## Recovery

Use the same common recovery engine:

```text
Abandonment
→ Risk
→ Root Cause
→ Decision
→ Policy
→ Payment Link
→ Payment
→ Webhook
→ Recovery
```
