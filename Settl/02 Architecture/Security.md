# Security

## Secrets

Keep these only on the backend:

- RAZORPAY_KEY_ID
- RAZORPAY_KEY_SECRET
- RAZORPAY_WEBHOOK_SECRET
- LLM_API_KEY

## Rules

- Never expose Razorpay secret keys in Next.js client code.
- Verify Razorpay webhook signatures.
- Scope database access by merchant ID.
- Store only necessary customer data.
- Never store card credentials.
- Use HTTPS for deployed webhooks.
- Treat external API responses as untrusted until validated.
- Log business metadata, not sensitive payment credentials.
