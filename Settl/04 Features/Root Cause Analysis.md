# Root Cause Analysis

## Purpose

Normalize the reason a revenue event became at risk.

## Example categories

- temporary payment failure
- insufficient funds
- repeated failure
- checkout abandonment
- subscription payment failure
- overdue receivable

## Grounding requirement

The explanation must cite the supplied fields it relied on.

Example:

> Temporary payment failure. The event contains `temporary_bank_failure`, and the customer has a strong recent payment history.

Never invent a bank response or customer intent that is not in the input.
