# ADR-002 — Use Supabase Queues Initially

**Status:** Accepted

## Decision

Use Supabase Queues instead of Redis/Celery for the initial implementation.

## Why

Settl needs asynchronous event/action processing but does not initially require a distributed queue platform.

This reduces:

- infrastructure
- setup time
- deployment complexity
- number of moving parts

## Revisit when

- throughput becomes a real bottleneck
- queue requirements exceed current capabilities
- production-scale deployment becomes necessary
