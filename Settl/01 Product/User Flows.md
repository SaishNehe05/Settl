# User Flows

## Flow 1 — Failed payment recovery

```text
Payment fails
→ Revenue event
→ Risk scoring
→ Root cause
→ Recovery decision
→ Policy gate
→ Payment Link
→ Customer payment
→ Razorpay webhook
→ Verify amount
→ RECOVERED
→ Dashboard + audit
```

## Flow 2 — Blocked recovery

```text
Revenue event
→ AI recommends recovery
→ Policy engine checks limits
→ Limit reached
→ BLOCK / STOP / ESCALATE
→ No financial action
→ Audit trail
```

## Flow 3 — Checkout abandonment

```text
Checkout started
→ No successful payment within timeout
→ CHECKOUT_ABANDONED
→ Risk scoring
→ Recovery decision
→ Policy
→ Payment Link
→ Payment
→ Webhook
→ RECOVERED
```
