# Settl — Build PRD

## Product

**Settl** is an AI-powered revenue recovery platform for merchants.

## Track

Razorpay Buildathon — Track 03: AI Revenue Recovery.

## Core problem

Revenue slips away when:

- payments fail
- checkout is abandoned
- recurring payments fail
- receivables become overdue

The hard problem is not merely finding the event. The system must decide whether the revenue is worth pursuing, choose the right intervention, execute it safely, verify the outcome, and measure the money actually recovered.

## Product promise

> Settl does not just identify lost revenue. It decides what can safely be recovered, executes the recovery workflow, verifies the result, and measures the revenue brought back.

## Primary user

Merchant / finance-operations user.

## Primary workflow

Failed payment recovery.

## Secondary workflow

Checkout abandonment recovery.

## Stretch workflow

Subscription recovery.

## Architecture principle

**LLM recommends → policy engine authorizes → Razorpay executes → webhook verifies**

## Goals

1. Detect revenue at risk.
2. Estimate recovery likelihood.
3. Explain the likely cause.
4. Recommend an intervention.
5. Enforce deterministic guardrails.
6. Execute an approved Razorpay recovery action.
7. Verify successful payment through server-side events.
8. Maintain a complete audit trail.
9. Measure recovery across a batch.

## Non-goals

- Generic chatbot.
- Direct LLM control of financial actions.
- Replacing Razorpay's payment processor.
- Unlimited retries.
- Pretending synthetic results are real payments.
- Building every example direction in Track 03 before the primary loop works.

## Definition of recovered revenue

A case counts as **RECOVERED** only after Settl receives and verifies a successful Razorpay payment event that is unambiguously linked to the recovery case and whose verified amount matches the expected recovery amount.

## Product principles

- Safety over automation.
- Evidence over claims.
- Small working loop before breadth.
- Deterministic controls around AI.
- Synthetic scale + real Test Mode proof.
- Every important financial action is auditable.
