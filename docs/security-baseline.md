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

- Azure resources are created only through the approved Terraform/GitHub Actions deployment flow.
- GitHub Actions authenticates to Azure through OIDC federated credentials, not stored client secrets.
- Cloud services should use managed identity where possible.
- Secrets should be stored in Azure Key Vault or GitHub secrets only when they cannot be replaced with managed identity.
- Terraform state must be stored in the Azure Storage backend created by the bootstrap script and treated as sensitive operational data.
