# System Architecture

## Final recommended stack

### Frontend

- Next.js
- TypeScript
- App Router
- Tailwind CSS
- shadcn/ui
- Recharts

### Backend

- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- psycopg

### Platform

- Supabase PostgreSQL
- Supabase Auth
- Supabase Queues
- Supabase Cron

### AI/ML

- scikit-learn
- Structured-output LLM interface

### Payments

- Razorpay Test Mode
- Razorpay Python SDK / REST APIs
- Payment Links
- Payment Link notifications
- Webhooks

### Testing

- pytest
- Playwright

### Deployment

- Vercel
- Railway
- Supabase

## Why not Redis initially?

We do not need another infrastructure service for the first version. Use Supabase Queues for durable async work.

## Why one backend?

Do not create many microservices. Use modular services inside one FastAPI application.
