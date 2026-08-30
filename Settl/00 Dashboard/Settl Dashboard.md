# Settl Dashboard

> **Settl — AI Revenue Recovery Agent**

**Track:** Razorpay Buildathon — Track 03: AI Revenue Recovery  
**Status:** 🟢 Phase 2 (Core Recovery Engine) Complete — Ready for Phase 3  
**Current milestone:** M3 — AI (Structured Root Cause & Decision Agent)

---

## Current Focus (Phase 3)

- [x] Implement revenue event ingestion (`POST /api/v1/events`) & simulation
- [x] Implement recovery case transactional state machine (`NEW` -> `APPROVED`/`BLOCKED`/`ESCALATED`)
- [x] Implement deterministic baseline risk scoring model (calibrated probability & priority)
- [x] Implement deterministic policy engine guardrails (attempts, limits, opt-out, cooldown)
- [x] Implement append-only audit logging service
- [x] Interactive UI: Simulation modal + Case action buttons (evaluate/approve/reject)
- [x] Verified via 22 unit tests (22/22 passed in 2.51s) & browser subagent
- [ ] Implement structured LLM root-cause analysis
- [ ] Implement structured recovery decision output
- [ ] Validate model outputs with Pydantic schemas

## Progress

| Milestone                 | Status | Notes                                                 |
| ------------------------- | ------ | ----------------------------------------------------- |
| M1 — Foundation           | ✅      | FastAPI + Next.js + Alembic + Seed data live          |
| M2 — Core Recovery        | ✅      | Ingestion, state machine, risk engine, policy guardrails, audit trail |
| M3 — AI                   | 🔄     | Grounded root-cause explainer + decision agent        |
| M4 — Guardrails           | ⬜      | Escalations, cooldowns, attempt caps                  |
| M5 — Razorpay             | ⬜      | Test Mode Payment Link + webhook receiver             |
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
