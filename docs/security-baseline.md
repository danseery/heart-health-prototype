# Security Baseline

The prototype is local-only, but it starts with production-shaped security boundaries so we do not have to retrofit them later.

## Data Handling

- Assessment answers, risk results, AI reports, and chat messages are treated as sensitive health data.
- Demo seed data must be synthetic.
- Sensitive payloads should stay behind backend repository/service methods.
- Logs and audit events must not include raw health values, AI prompts, chat transcripts, secrets, or tokens.

## Application Controls

- Backend validation is server-side and schema-driven.
- CORS is limited to local frontend origins by default.
- Security headers are added by middleware.
- Error responses should be structured and should not expose stack traces.
- Ownership checks should be implemented even for demo users.

## AI Controls

- The default local AI provider is dummy and deterministic.
- AI responses must include educational-only disclaimers.
- AI responses should cite source content when generated from content.
- User prompts are untrusted and must not override system rules or reveal hidden prompts.

## Cloud Readiness

- No Azure resources are created during local prototype work.
- Future cloud services should use managed identity where possible.
- Secrets should move to Azure Key Vault only after infrastructure work is approved.
