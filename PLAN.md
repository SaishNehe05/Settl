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

## Phase 4 Status: ✅ Complete & Running

- Razorpay Test Mode client integration with paise money units
- Payment Links creation with idempotency and case metadata tracking
- Raw request body HMAC-SHA256 signature verification
- `payment_link.paid` webhook receiver with strict amount verification
- Real-time state transition to `RECOVERED` with emerald proof banner
- 34/34 unit and integration tests passing in 2.51s

---

## Phase 5: Real End-to-End Test Loop Implementation Plan

### 1. Primary Recovery Case Loop (₹8,499)
- **Customer:** Arjun Mehta (high-value tier, 85% success rate, consent active).
- **Failure:** `temporary_bank_failure` (₹8,499).
- **Execution:** Event &rarr; Risk Engine (86.8%) &rarr; AI Root Cause (`BANK_TECHNICAL`) &rarr; Decision (`CREATE_PAYMENT_LINK`) &rarr; Policy Gate (`ALLOW`) &rarr; Razorpay Payment Link (`plink_...`) &rarr; Payment &rarr; Verified Webhook &rarr; Terminal State: `RECOVERED`.

### 2. Guardrail Stopping Rule Demonstration
- **Customer:** Priya Nair (opted out: `opted_out = True`).
- **Failure:** `insufficient_funds` (₹3,200).
- **Enforcement:** Policy Engine detects opt-out, immediately evaluates to `BLOCK`, halts outreach, creates zero payment links, transitions to `BLOCKED`, and records audit proof.

### 3. High-Value Escalation Demonstration
- **Customer:** Rajesh Sharma (₹45,000 failure).
- **Enforcement:** Amount exceeds ₹10,000 threshold &rarr; transitions to `ESCALATED` awaiting human operator review. Operator approves &rarr; transitions to `APPROVED`.

### 4. Verification Deliverables
- Automated integration test `tests/test_end_to_end_loop.py`.
- Browser subagent visual demonstration of both cases and dashboard metrics.
- Complete documentation in Obsidian vault and walkthrough artifact.



