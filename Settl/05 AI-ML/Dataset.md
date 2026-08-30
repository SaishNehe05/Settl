# Dataset

## Goal

Create a synthetic but structured revenue-loss dataset with known ground truth.

## Target

5,000 events.

Suggested mix:

- 2,000 payment failures
- 1,500 checkout abandonments
- 1,000 subscription failures
- 500 overdue receivables

## Required fields

```text
event_id
event_type
amount_paise
failure_reason
attempt_count
customer_success_rate
customer_value
opted_out
recoverable
ideal_action
successful_recovery
recovered_amount_paise
```

## Split

Preferred:

- 70% development
- 15% validation
- 15% locked test

Alternative:

- 4,000 development
- 1,000 locked test

Never tune on locked test data.
