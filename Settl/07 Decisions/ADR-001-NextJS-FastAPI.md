# ADR-001 — Next.js + FastAPI

**Status:** Accepted

## Decision

Use Next.js for the frontend and FastAPI for the backend.

## Context

Settl requires:

- merchant dashboard
- AI/ML
- Razorpay integration
- webhooks
- relational database operations

## Choice

Next.js:

- dashboard
- routing
- authentication UI
- API client

FastAPI:

- AI orchestration
- ML
- recovery workflow
- Razorpay integration
- webhooks
- policy enforcement

## Why

Python is the natural home for the ML/AI layer, while Next.js provides a strong typed React frontend.

## Consequence

Two application layers must be maintained, but responsibilities stay clear.
