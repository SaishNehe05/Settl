# Current Sprint

## Sprint Goal

Phase 2 (Core Recovery Engine) complete! Transitioning into **Phase 3 — AI (Structured Root Cause & Decision Agent)**.

## Completed (Phase 1 — Foundation)

- [x] Create Settl repository and folder structure (`apps/api`, `apps/web`, `scripts`)
- [x] Set up Next.js 15 App Router merchant portal with TypeScript & Tailwind CSS
- [x] Set up FastAPI + Pydantic v2 + SQLAlchemy 2.0 backend
- [x] Configure environment variables and connect live Supabase PostgreSQL
- [x] Implement 12 core database tables with money strictly in paise as `BIGINT`
- [x] Create & run Alembic migration `0001_initial_schema` against Supabase
- [x] Seed Supabase database with default merchant, policy, customers, and cases (including primary ₹8,499 case)
- [x] Add JWT Bearer authentication and merchant tenant isolation
- [x] Write backend unit tests (7/7 passed in `pytest`)
- [x] Validate frontend compilation and browser UI

## Completed (Phase 2 — Core Recovery Engine)

- [x] Implement revenue event ingestion (`POST /api/v1/events`) with idempotency and auto-provisioning
- [x] Implement simulation injector (`POST /api/v1/events/simulate`)
- [x] Implement recovery case transactional state machine (`NEW` -> `ANALYZING` -> `READY` -> `POLICY_CHECK` -> `APPROVED` | `BLOCKED` | `ESCALATED`)
- [x] Implement deterministic baseline risk scoring engine (calibrated probability, priority, candidate actions)
- [x] Implement deterministic policy engine (attempts cap, ₹10,000 threshold, opt-out, probability, cooldown)
- [x] Implement append-only audit logging service for financial integrity
- [x] Implement operator review endpoints (`/approve`, `/reject`)
- [x] Add interactive UI controls: Simulate Leakage Event modal + Case action buttons
- [x] Expand automated test suite to 22 tests (22/22 passed in 2.51s)
- [x] Verified full browser event simulation and escalation flow

## Completed (Phase 3 — AI)

- [x] Implement structured LLM root-cause analysis with Pydantic contracts
- [x] Implement structured recovery decision output & channel recommendations
- [x] Validate model outputs with strict Pydantic schemas (`RootCauseAnalysisOutput`, `RecoveryDecisionOutput`)
- [x] Ensure ML/risk probability remains strictly in the mathematical risk layer
- [x] Model prediction audit logging to Supabase `model_predictions` table
- [x] Rejection of unsupported actions (e.g. attempting to auto-debit cards)
- [x] Zero-crash deterministic fallback engine
- [x] Case Detail UI displays structured evidence tags, channel recommendations, and model trace
- [x] Test suite expanded to 27 tests (27/27 passed in 2.48s)

## Doing (Phase 4 — Razorpay Test Mode & Webhooks)

- [ ] Implement Razorpay Test Mode client configuration
- [ ] Implement Razorpay Payment Links creation service
- [ ] Implement idempotency keys and duplicate protection
- [ ] Implement Razorpay raw webhook signature verification
- [ ] Handle `payment_link.paid` webhook
- [ ] Verify payment amount and transition case to `RECOVERED`

## Blocked

None.

## Next Sprint

Phase 5 — End-to-End Test (Live ₹8,499 case recovery & guardrail demonstration).
