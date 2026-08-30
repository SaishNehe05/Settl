# AI Coding Agent Checklist

Use this whenever asking a coding AI to change Settl.

## Before coding

- [ ] Point it to the relevant PRD section.
- [ ] Point it to the relevant TDD section.
- [ ] Tell it which files may change.
- [ ] Ask for a small implementation step.

## During coding

- [ ] Do not allow architecture changes without explanation.
- [ ] Do not allow invented Razorpay APIs.
- [ ] Do not allow secrets in frontend code.
- [ ] Do not let LLM code bypass policy checks.

## After coding

- [x] Run tests. (41/41 passed in pytest in 2.71s)
- [x] Run type checks/lint. (Next.js build succeeded in 15.0s)
- [x] Run application. (FastAPI on :8000, Next.js on :3000 live)
- [x] Verify the intended flow. (Browser verified all 5 pages: Overview, Queue, Case Detail, Policies, Evaluation)
- [x] Inspect generated code.
- [x] Update Obsidian.
- [x] Mark completed work.

## Rule

> Build incrementally. Do not ask the coding AI to build the entire project in one shot.
