# Scope

## P0 — Must Build

- Event ingestion
- Revenue-risk scoring
- Root-cause analysis
- Recovery decision agent
- Policy engine
- Recovery case state machine
- Payment Link creation
- Razorpay webhook verification
- Recovery ledger
- Audit trail
- Merchant dashboard

## P1 — Build after P0 works

- Checkout abandonment detection
- Checkout recovery workflow
- Locked evaluation set
- Evaluation dashboard

## P2 — Stretch

- Subscription recovery
- Advanced notifications
- More recovery channels
- Merchant-specific model tuning

## Explicitly postponed

- Voice recovery
- B2B receivables
- Mandate retry sequencer
- Multi-agent orchestration frameworks
- Multiple LLM providers
- Vector database / RAG
- Microservice deployment

## Scope rule

Do not start a P1 feature while the primary failed-payment recovery loop is broken.
