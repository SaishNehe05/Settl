# Settl Dashboard

> **Settl — AI Revenue Recovery Agent**

**Track:** Razorpay Buildathon — Track 03: AI Revenue Recovery  
**Status:** 🟢 Phase 3 (AI Engine) Complete — Ready for Phase 4  
**Current milestone:** M4 — Razorpay Test Mode & Webhooks (Phase 4)

---

## Current Focus (Phase 4)

- [x] Structured LLM root-cause analysis with Pydantic contracts
- [x] Structured recovery decision output & channel recommendations
- [x] Rejection of unsupported actions & zero-crash fallback engine
- [x] Model prediction logging to Supabase `model_predictions` table
- [x] Interactive UI with grounded evidence tags & model traces
- [x] 27 unit and integration tests (27/27 passed in 2.48s)
- [ ] Implement Razorpay Test Mode client & Payment Links service
- [ ] Implement idempotency keys and duplicate protection
- [ ] Implement Razorpay raw webhook signature verification
- [ ] Handle `payment_link.paid` webhook to confirm recovery

## Progress

| Milestone                 | Status | Notes                                                 |
| ------------------------- | ------ | ----------------------------------------------------- |
| M1 — Foundation           | ✅      | FastAPI + Next.js + Supabase live          |
| M2 — Core Recovery        | ✅      | Ingestion, state machine, risk engine, policy guardrails, audit trail |
| M3 — AI                   | ✅      | Structured root cause, bounded decisions, Pydantic validation, model logging |
| M4 — Guardrails           | ✅      | Deterministic attempt limits, amounts, opt-out, cooldown (built in P2) |
| M5 — Razorpay             | 🔄     | Test Mode Payment Link + webhook receiver (Phase 4) |
| M6 — Closed Loop          | ⬜      | Live verified payment recovery of ₹8,499 case         |
| M7 — Checkout Abandonment | ⬜      | Secondary lifecycle recovery workflow                 |
| M8 — Evaluation           | ⬜      | 5k synthetic benchmark + locked test set              |
| M9 — Polish               | ⬜      | Performance, telemetry, and final polish              |

---

## Product Goal

Build a system that:

**Detects → Diagnoses → Decides → Guards → Executes → Verifies → Measures**

Primary live workflow:

**Failed payment → recovery decision → policy gate → Razorpay Payment Link → payment → webhook → verified recovered revenue**

---

## Current Live Baseline Metrics (Seeded Data)

- Revenue at Risk: **₹66,699**
- Eligible Revenue: **₹55,999**
- Revenue Recovered: **₹12,500** (historic baseline verified)
- Recovery Rate: **22.3%**
- Guardrail Blocks: **2** (max attempts + opt-out)
- Human Escalations: **1** (₹35k > ₹10k threshold)
- Total Active Cases: **4**
- Detection Precision: — (Target: Phase 6)
- Detection Recall: — (Target: Phase 6)
- Decision Accuracy: — (Target: Phase 6)
- Policy Violations: **0**

---

## Current Blocker

None. Native local environment (Python 3.13 + Node.js 22) verified and working cleanly.

## Next Task

Begin **PHASE 2 — CORE RECOVERY ENGINE**:
1. Event ingestion endpoint `POST /api/v1/events`.
2. Recovery case transactional state machine.
3. Feature builder and deterministic baseline risk scoring model.
4. Policy engine rule enforcement.
5. Append-only audit logger.

## Quick Links

- [[01 Product/PRD]]
- [[01 Product/Scope]]
- [[02 Architecture/TDD]]
- [[02 Architecture/System Architecture]]
- [[02 Architecture/Database Design]]
- [[02 Architecture/Razorpay Integration]]
- [[03 Development/Roadmap]]
- [[03 Development/Current Sprint]]
- [[03 Development/Backlog]]
- [[05 AI-ML/Dataset]]
- [[05 AI-ML/Model Experiments]]
- [[06 Testing/Bugs]]
- [[07 Decisions/ADR-001-NextJS-FastAPI]]
- [[10 Demo/Demo Flow]]
