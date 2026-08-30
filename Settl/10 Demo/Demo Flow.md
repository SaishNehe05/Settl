# Demo Flow

## 1. Dashboard

Show:

- Revenue at Risk
- Eligible Revenue
- Revenue Recovered
- Recovery Rate

## 2. Select a failed-payment case

Show:

- amount
- failure reason
- customer history
- recovery probability
- expected recovery value

## 3. Show AI decision

Show:

- root cause
- recommended action
- reasoning

## 4. Show policy gate

Show:

- attempt limit
- amount limit
- cooldown
- customer eligibility
- result: ALLOW

## 5. Execute

Create a Razorpay Test Mode Payment Link.

## 6. Complete test payment

Customer completes payment.

## 7. Webhook

Show `payment_link.paid`.

## 8. Recovery

Dashboard changes to:

**Recovered**

## 9. Show failure handling

Use a max-attempts case.

Policy blocks the recovery.

## 10. Audit

Show complete timeline.

## 11. Evaluation

Show locked batch metrics.
