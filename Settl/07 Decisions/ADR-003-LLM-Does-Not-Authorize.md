# ADR-003 — LLM Does Not Authorize Financial Actions

**Status:** Accepted

## Decision

The LLM can recommend an action but cannot authorize or directly execute financial actions.

## Architecture

```text
LLM recommendation
→ deterministic policy
→ approved command
→ executor
```

## Reason

Financial actions need deterministic controls for:

- limits
- customer consent/opt-out
- cooldown
- attempts
- escalation
- amount integrity

## Consequence

Even if the LLM behaves incorrectly, policy rules can block the financial action.
