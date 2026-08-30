# Razorpay Integration

## Primary recovery mechanism

Razorpay Payment Links.

## Main flow

```text
Settl
  ↓
POST /v1/payment_links
  ↓
Payment Link
  ↓
Customer
  ↓
Razorpay payment
  ↓
payment_link.paid
  ↓
Settl webhook
  ↓
Verification
  ↓
Recovered
```

## Required operations

- Create Payment Link
- Fetch Payment Link when needed
- Send/resend supported notification
- Receive Payment Link webhook
- Verify webhook signature
- Verify amount and recovery reference

## Important rules

- Razorpay secret keys stay on backend.
- Never trust browser redirects for accounting.
- Webhook is the authoritative server-side event for recovery accounting.
- Never mark RECOVERED merely because Payment Link creation returned 200.
- Verify the successful payment amount before crediting recovered revenue.
- Use a unique recovery reference per case.
- Prevent duplicate Payment Links.

## Test Mode planning

Large batch evaluation is synthetic.

Real Razorpay Test Mode is used for representative end-to-end cases.

Do not attempt thousands of real Payment Links in Test Mode.
