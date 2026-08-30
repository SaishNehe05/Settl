# Settl — Implementation Plan & Phase 1 + Phase 2

**Project:** Settl — Autonomous Revenue Recovery Agent  
**Track:** Razorpay Buildathon — Track 03: AI Revenue Recovery  
**Core Principle:** *AI recommends; deterministic policy code authorizes; Razorpay executes; verified webhook events confirm recovery.*

---

## Phase 1 Status: ✅ Complete & Running

- Repository layout: `apps/api`, `apps/web`, `scripts`
- FastAPI backend + SQLAlchemy 2.0 + Pydantic v2
- Connected live to Supabase PostgreSQL (`aws-0-ap-south-1.pooler.supabase.com:6543`)
- 12 core tables migrated and seeded with paise as `BIGINT`
- Next.js 15 App Router portal running on :3000
- 7/7 backend unit tests passing

---

## Phase 2: Core Recovery Engine Implementation Plan

### 1. Objectives
1. **Event Ingestion (`POST /api/v1/events`):**
   - Normalization of incoming payment failures and abandonments.
   - Deduplication and idempotency.
   - Dynamic customer provisioning / linking.
   - Automatic `RecoveryCase` instantiation.
2. **Recovery Case State Machine:**
   - Transactional transitions:
     `NEW` → `ANALYZING` → `READY` → `POLICY_CHECK` → (`APPROVED` | `BLOCKED` | `ESCALATED`)
3. **Deterministic Baseline Risk Engine:**
   - Feature extraction (`amount_paise`, `failure_reason`, `customer_success_rate`, `customer_value`, `attempt_count`, `opted_out`).
   - Calibrated numerical `recovery_probability` ($0.0 - 1.0$) and `priority` (`LOW`, `MEDIUM`, `HIGH`, `URGENT`).
   - Grounded candidate action selection.
4. **Deterministic Policy Engine:**
   - Evaluates actions against guardrails:
     - `attempt_count >= max_attempts` → `BLOCKED` (`MAX_ATTEMPTS_REACHED`)
     - `amount > max_automated_amount` → `ESCALATED` (`AMOUNT_REQUIRES_HUMAN`)
     - `recovery_probability < min_probability` → `BLOCKED` (`LOW_RECOVERY_PROBABILITY`)
     - `customer.opted_out == True` → `BLOCKED` (`CUSTOMER_OPTOUT`)
     - Cooldown active → `WAIT` (`COOLDOWN_ACTIVE`)
5. **Append-Only Audit Logging Service:**
   - Verifiable timeline creation on every transition.
6. **Dashboard Execution Hooks:**
   - Quick simulation button for live testing.
   - On-demand policy evaluation trigger.
   - Operator human review actions (Approve / Reject).

### 2. File Changes
- **Backend:**
  - `apps/api/app/services/event_service.py` [NEW]
  - `apps/api/app/services/recovery_service.py` [NEW]
  - `apps/api/app/services/policy_service.py` [NEW]
  - `apps/api/app/services/audit_service.py` [NEW]
  - `apps/api/app/agents/risk_engine.py` [NEW]
  - `apps/api/app/api/v1/events.py` [NEW]
  - `apps/api/app/api/v1/cases.py` [MODIFY]
  - `apps/api/app/api/v1/router.py` [MODIFY]
- **Tests:**
  - `apps/api/tests/test_event_service.py` [NEW]
  - `apps/api/tests/test_risk_engine.py` [NEW]
  - `apps/api/tests/test_policy_engine.py` [NEW]
  - `apps/api/tests/test_state_machine.py` [NEW]
## Phase 2 Status: ✅ Complete & Running

- Event ingestion (`POST /api/v1/events`) with idempotency and simulation injector
- Transactional state machine (`NEW` -> `ANALYZING` -> `READY` -> `POLICY_CHECK` -> `APPROVED` | `BLOCKED` | `ESCALATED`)
- Calibrated deterministic baseline risk engine (recovery probability & priority)
- Deterministic policy engine with 6 guardrails
- Append-only audit logger
- 22/22 unit tests passing in 2.51s
- UI: Simulate Leakage Event modal + Case action buttons (evaluate/approve/reject)

---

## Phase 3 Status: ✅ Complete & Running

- Pydantic structured output contracts (`RootCauseAnalysisOutput`, `RecoveryDecisionOutput`)
- AI orchestration service with zero-downtime deterministic fallback
- Rejection of unsupported actions
- Model prediction persistence in Supabase `model_predictions` table
- Interactive UI: Diagnostic root-cause cards, grounded evidence tags, model trace
- 27/27 unit tests passing in 2.48s

---

## Phase 4: Razorpay (Test Mode & Webhooks) Implementation Plan

### 1. Objectives
1. **Razorpay Service (`services/razorpay_service.py`):**
   - Official Razorpay SDK integration for Test Mode.
   - Payment Links creation with paise amounts, custom reference IDs, and case metadata notes.
   - Idempotency & duplicate protection.
   - HMAC-SHA256 raw webhook signature verification.
2. **State Machine Execution Transition:**
   - `APPROVED` -> `EXECUTING` -> Razorpay API -> `WAITING_RESULT`.
   - Records `RecoveryAction` with `razorpay_entity_id`.
3. **Raw Webhook Receiver (`POST /api/v1/webhooks/razorpay`):**
   - Signature verification using raw request bytes.
   - Idempotency check via `webhook_events` table.
   - Handles `payment_link.paid`.
   - Strictly verifies `paid_amount_paise >= case.amount_at_risk_paise`.
   - Transitions case to `RECOVERED`.
   - Appends audit log with webhook actor.
4. **Interactive UI Capabilities:**
   - "Generate Razorpay Payment Link" button for approved cases.
   - Active payment link display with URL copy and "Simulate Customer Payment" test button.


