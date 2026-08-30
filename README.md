# Settl — Autonomous AI Revenue Recovery Agent

> **Razorpay Buildathon — Track 03: AI Revenue Recovery**  
> *AI recommends; deterministic policy code authorizes; Razorpay executes; verified webhook events confirm recovery.*

---

## Overview

Settl recovers legitimate revenue at risk after customer payment failure or checkout abandonment. It bridges AI-assisted recovery decisions with deterministic financial guardrails and verifiable Razorpay execution.

## Tech Stack

- **Frontend:** Next.js 15 (App Router), TypeScript, Tailwind CSS, Lucide Icons
- **Backend:** FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic
- **Database:** Supabase PostgreSQL / local SQLite
- **Payments:** Razorpay Test Mode Payment Links & Webhooks
- **ML / AI:** Scikit-Learn baseline + Structured Output LLM Agents

## Quickstart (Local Development)

### 1. Backend

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
alembic upgrade head
python -m app.scripts.seed_db
uvicorn app.main:app --reload --port 8000
```
Swagger API docs will be at: `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd apps/web
npm install
npm run dev
```
Merchant portal will be at: `http://localhost:3000`.

### 3. Tests

```bash
cd apps/api
pytest -v
```
