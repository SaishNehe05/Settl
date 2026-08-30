# Test Plan

## Unit tests

- [ ] Policy rules
- [ ] Amount calculations
- [ ] Recovery probability calculations
- [ ] State transitions
- [ ] Idempotency helpers

## Integration tests

- [ ] Database transactions
- [ ] Razorpay client mocked responses
- [ ] Webhook verification
- [ ] Payment Link service

## Agent tests

- [ ] Valid structured output
- [ ] Invalid JSON
- [ ] Unsupported action
- [ ] Grounded explanation
- [ ] No amount modification

## Webhook tests

- [ ] Valid signature
- [ ] Invalid signature
- [ ] Duplicate webhook
- [ ] Malformed payload
- [ ] Amount mismatch

## E2E

- [ ] Failed payment → recovery case
- [ ] Case → Payment Link
- [ ] Payment → webhook
- [ ] Webhook → recovered
- [ ] Blocked case → no financial action

## Evaluation

- [ ] Locked 5k batch
- [ ] Stable reproducibility
