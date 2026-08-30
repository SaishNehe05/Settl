# Settl — Technical Design Document

See the full implementation TDD in the project documentation.

## Core architecture

```text
Browser
  ↓
Next.js
  ↓
FastAPI
  ├─ Event Processing
  ├─ Recovery Service
  ├─ AI Orchestration
  ├─ Policy Engine
  ├─ Razorpay Client
  ├─ Webhook Receiver
  └─ Evaluation
  ↓
Supabase PostgreSQL
  ├─ Auth
  ├─ Queues
  └─ Cron
  ↓
Python Worker
  ↓
Razorpay Test Mode
```

## Core design rule

The LLM never directly executes a financial action.

## First end-to-end milestone

Seeded failed payment:

**failed event → recovery case → policy allow → Payment Link → test payment → payment_link.paid → verified RECOVERED**
