# Demo Data

## Primary happy-path case

Customer:

Demo Customer

Order:

ORD_1042

Amount:

₹8,499

Event:

PAYMENT_FAILED

Failure:

temporary_bank_failure

Attempts:

0

Customer success rate:

87.5%

Expected:

High recovery probability → Payment Link → successful Test Mode payment → recovered.

## Guardrail case

Amount:

₹8,499

Attempts:

2

Maximum attempts:

2

Expected:

Policy blocks action.
