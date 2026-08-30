# Webhook Processing

## Endpoint

`POST /api/v1/webhooks/razorpay`

## Process

```text
Raw request body
→ Read signature
→ Verify signature
→ Deduplicate
→ Persist event
→ Normalize
→ Queue processing
```

## Payment Link recovery event

`payment_link.paid`

## Verification

Before marking recovered:

- webhook signature valid
- event not duplicate
- recovery case exists
- Payment Link belongs to recovery case
- payment is successful
- amount matches expected amount

## Invalid event

Do not update financial state.
Log the security/processing failure.
