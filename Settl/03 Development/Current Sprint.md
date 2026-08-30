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

## Completed (Phase 4 — Razorpay Test Mode & Webhooks)

- [x] Implement Razorpay Test Mode client configuration
- [x] Implement Razorpay Payment Links creation service in paise
- [x] Implement idempotency keys and duplicate protection
- [x] Implement Razorpay raw webhook signature verification (HMAC-SHA256)
- [x] Handle `payment_link.paid` webhook
- [x] Strictly verify payment amount (`paid >= amount_at_risk_paise`)
- [x] Transition case to `RECOVERED`, record action as `SUCCESS`, log audit trail
- [x] Webhook simulation endpoint (`POST /api/v1/webhooks/razorpay/simulate`)
- [x] Interactive UI: Create Payment Link button, live link card, and Simulate Webhook Payment trigger
- [x] Visual verification in browser: clean failure -> APPROVED -> WAITING_RESULT -> RECOVERED
- [x] Test suite expanded to 34 tests (34/34 passed in 2.51s)

## Completed (Phase 5 — Real End-to-End Test Loop)

- [x] Execute and verify primary ₹8,499 case (`CASE_8499_RECOVERABLE`) from failure to verified recovery
- [x] Verify state machine progression through all 8 steps to RECOVERED with emerald proof banner
- [x] Demonstrate secondary guardrail stopping rule: `CASE_OPTOUT` (customer opt-out strictly enforced, zero links generated)
- [x] Demonstrate secondary guardrail stopping rule: `CASE_MAX_ATTEMPTS` (attempt ceiling stops outreach)
- [x] Demonstrate high-value escalation rule: `CASE_HIGH_VALUE` (₹35,000 halts in ESCALATED awaiting human review)
- [x] Automated end-to-end integration test suite (`tests/test_end_to_end_loop.py`)
- [x] Expanded test suite to 38 tests (38/38 passed in 2.67s)
- [x] Verified real-time dashboard metric aggregation in live browser session

## Completed (Phase 6 — Evaluation & Benchmark Harness)

- [x] Create 5,000 synthetic events dataset generator with seed=42 (`app/evaluation/dataset_generator.py`)
- [x] Implement 4,000 dev / 1,000 locked test dataset split (`evaluation_dev_4000.json`, `evaluation_locked_test_1000.json`)
- [x] Ground-truth recoverability labels (`is_recoverable`, `optimal_action`, `optimal_channel`)
- [x] Run offline simulation benchmark with precision, recall, net recovered revenue, and false positive metrics
- [x] Ensure strict isolation between simulation evaluation and live Razorpay test actions (preserving 30-link quota)
- [x] Build interactive Next.js Evaluation Dashboard UI (`/evaluation`) with comparative table and confusion matrix
- [x] Automated test suite expanded to 41 tests (41/41 passed in 2.71s)
- [x] Visual verification of Evaluation Dashboard in live browser session

## Doing (M9 — Final Polish & Submission Package)

- [ ] End-to-end repository review and dead code cleanup
- [ ] Buildathon submission package and walkthrough video summary
- [ ] Final verification of all pages (`/`, `/cases`, `/cases/[id]`, `/policies`, `/evaluation`)

## Blocked

None.

## Next Sprint

Official submission to Razorpay Buildathon — Track 03: AI Revenue Recovery.
