# Policy Engine

## Principle

The policy engine is deterministic.

The LLM cannot override it.

## Example rules

```text
attempts >= max_attempts
→ STOP

amount > max_automated_amount
→ ESCALATE

probability < min_probability
→ STOP

customer opted out
→ STOP

cooldown active
→ WAIT

action not allowed for event type
→ BLOCK

otherwise
→ ALLOW
```

## Default MVP values

- Max attempts: 2
- Max automated amount: ₹10,000
- Minimum probability: 0.40
- Cooldown: 240 minutes

These are development defaults, not permanent business policy.
