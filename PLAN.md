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

## Phase 3: AI (Root Cause & Decision Agent) Implementation Plan

### 1. Objectives
1. **Structured Output Schemas (`app/schemas/ai.py`):**
   - `RootCauseAnalysisOutput` (failure_category, summary, confidence, evidence, sentiment risk).
   - `RecoveryDecisionOutput` (strictly bounded action Literal, channel, delay_minutes, reasoning).
2. **AI Orchestration Service (`app/services/ai_service.py`):**
   - Provider abstraction (OpenAI / Gemini / Offline-ready reasoning engine).
   - Strict Pydantic schema validation.
   - Guardrails against unsupported actions (e.g. auto-charging cards).
   - Zero-crash fallback to deterministic baseline.
3. **Model Prediction Audit Logging:**
   - Persist all LLM inferences to `model_predictions` table.
4. **Integration with State Machine:**
   - Wire AI diagnosis & decision into `analyze_case(case_id)`.
   - Preserve numerical probability in the ML/risk layer.
5. **Interactive UI Display:**
   - AI diagnostic cards, evidence tags, channel recommendations, and model trace in Case Detail view.

