# Evaluation Engine

## Purpose

Run large-scale testing without making real Razorpay financial actions.

## Pipeline

```text
Synthetic Dataset
→ Normalize
→ Risk Model
→ Root Cause
→ Decision
→ Policy
→ Simulator
→ Metrics
```

## Metrics

- Precision
- Recall
- Decision Accuracy
- Recovery Rate
- Recovered Value
- Expected Value Error
- Policy Violations
- Duplicate Actions
- Throughput

## Important

The evaluation pipeline must use a locked test set that is not tuned against.
