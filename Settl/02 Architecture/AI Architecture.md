# AI Architecture

## Pipeline

```text
Revenue Event
   ↓
Feature Builder
   ↓
ML Risk Model
   ↓
Root Cause Agent
   ↓
Decision Agent
   ↓
Deterministic Policy Engine
   ↓
Action Executor
```

## ML responsibility

Produces numerical recovery probability.

Candidate models:

1. Logistic Regression
2. Gradient-boosted model only if it improves held-out results

## LLM responsibility

- Explain root cause using supplied evidence.
- Recommend an allowed action.
- Return strict structured output.

## LLM must not

- invent payment facts
- change the amount
- alter policy
- create new action types
- override customer opt-out
- authorize payment directly

## Model routing

Start with one reliable model.

Only add local/remote model routing after the complete recovery loop works.
