# End-to-End Tests

## Test 1 — Successful recovery

```text
Seed failed payment
→ Analyze
→ Policy ALLOW
→ Create Test Mode Payment Link
→ Complete payment
→ payment_link.paid
→ Verify
→ RECOVERED
```

Expected:

- one recovery action
- correct amount
- verified payment
- dashboard updated
- audit complete

## Test 2 — Stopping rule

```text
Seed case at max attempts
→ Analyze
→ Decision recommends recovery
→ Policy BLOCKS
→ No Payment Link
→ STOP/ESCALATE
```

Expected:

- zero financial actions
- audit contains reason
