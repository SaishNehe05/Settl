# Payment Link

## Purpose

Provide a new, bounded payment opportunity for an outstanding amount.

## Main API

`POST /v1/payment_links`

## Required protections

- unique `reference_id`
- exact expected amount
- expiry
- recovery case ID in notes/metadata
- no duplicate active link per case

## Important

Creating a Payment Link is **not** the same as recovering revenue.

Revenue becomes recovered only after verified successful payment.
