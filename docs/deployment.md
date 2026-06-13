# Azure Dev Deployment

This project uses Terraform and GitHub Actions to create a repeatable Azure dev environment. The dev environment is intentionally production-shaped and should not store real patient data yet.

## Resource Group Naming

The resource group is the environment anchor. For dev, the default is:

```text
rg-heart-health-dev
```

When production is ready, create a production tfvars file using:

```text
rg-heart-health-prod
```

Terraform derives the rest of the names from the resource group, for example:

- `acrhearthealthdev`
- `kv-heart-health-dev`
- `cae-heart-health-dev`
- `ca-heart-health-dev-api`
- `ca-heart-health-dev-web`

Azure Container Registry and Key Vault names are globally unique. If a derived name is already taken, set `global_name_suffix`, `container_registry_name`, or `key_vault_name` in the environment tfvars file.

## Dev Architecture

Terraform creates these resources in the environment resource group:

- Azure Container Registry with admin access disabled
- Azure Container Apps environment
- API container app for FastAPI
- Web container app for the React/Vite static frontend
- User-assigned managed identity for app resource access
- Key Vault using Azure RBAC
- Log Analytics workspace
- Application Insights
- Optional Azure OpenAI account in the environment resource group

The app deployment flow is:

1. GitHub Actions authenticates to Azure using OIDC.
2. Terraform creates the resource group, ACR, identity, Key Vault, logging, and Container Apps environment.
3. GitHub Actions builds and pushes frontend/API images to ACR.
4. Terraform creates or updates the Container Apps to run the pushed images.

## One-Time Bootstrap

GitHub Actions needs a federated Azure identity and remote Terraform state before it can deploy. Run this once from a machine where you are signed in to both Azure CLI and GitHub CLI:

Before running bootstrap, review the [bootstrap checklist](bootstrap-checklist.md)
or run the prerequisite check:

```bash
./scripts/bootstrap-azure-oidc.sh --check-prereqs
```

PowerShell:

```powershell
az login --tenant 98983dd6-f1f1-40e3-91f8-2bbf22020202
gh auth login
.\scripts\bootstrap-azure-oidc.ps1
```

Bash:

```bash
az login --tenant 98983dd6-f1f1-40e3-91f8-2bbf22020202
gh auth login
./scripts/bootstrap-azure-oidc.sh
```

The script creates:

- Terraform state resource group: `rg-heart-health-tfstate`
- Terraform state storage account and blob container
- Azure app registration/service principal for GitHub Actions
- Federated credential for the GitHub `dev` environment
- GitHub environment variables used by the deployment workflow

It does not create or store a client secret. GitHub Actions uses short-lived OIDC tokens.

## Deploy Dev

After bootstrap, run the `Deploy dev` workflow in GitHub Actions. It also runs automatically on pushes to `main` that touch app, infrastructure, or deploy workflow files.

The workflow expects these GitHub environment variables in the `dev` environment:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `TF_STATE_RESOURCE_GROUP_NAME`
- `TF_STATE_STORAGE_ACCOUNT_NAME`
- `TF_STATE_CONTAINER_NAME`
- `TF_STATE_KEY`

The bootstrap script sets these for you.

Set `AZURE_OPENAI_DEPLOYMENT` in the GitHub `dev` environment to the Azure
OpenAI deployment name the backend should use. Dev currently uses `gpt-5.4`.
The deploy workflow intentionally does not infer a deployment from the Azure
account because multiple chat, embedding, or test deployments may exist. The
workflow passes this as an explicit Terraform `-var` so it overrides the blank
deployment value kept in `infra/terraform/environments/dev.tfvars`.

No Big Brain API key is stored in GitHub secrets. After GitHub Actions signs in
to Azure with OIDC, the deploy workflow reads the key with Azure CLI, masks it in
logs, and passes it to Terraform only for that workflow run. The federated Azure
identity must have permission to list keys on the Big Brain
`Microsoft.CognitiveServices/accounts` resource.

## Azure OpenAI

Dev is configured for the `big-brain` Azure OpenAI resource:

```text
AI_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://big-brain.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-5.4
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

The backend can now route completed assessment summaries to Big Brain when
`AI_PROVIDER=azure_openai` is set. Azure AI Foundry endpoints ending in
`.services.ai.azure.com` use `/models/chat/completions`; Azure OpenAI endpoints
ending in `.openai.azure.com` use `/openai/deployments/{deployment}/chat/completions`.
For deployed environments, store keys in Key Vault or move this integration to
managed identity before handling real user data.

If you want Azure OpenAI created inside `rg-heart-health-dev` instead of pointing to the existing Foundry resource, set:

```hcl
create_azure_openai_resource = true
azure_openai_endpoint        = ""
```

Azure OpenAI model quota and deployment availability can vary by subscription and region, so the first model deployment may still require a capacity check in Azure AI Foundry.

## Production Path

For production:

1. Copy `infra/terraform/environments/prod.tfvars.example` to `prod.tfvars`.
2. Set `resource_group_name = "rg-heart-health-prod"`.
3. Set the production Azure OpenAI endpoint and deployment.
4. Run the bootstrap script with `-EnvironmentName prod`, `-StateKey heart-health-prod.tfstate`, and a production app registration name.
5. Add a production deployment workflow or generalize the dev workflow to accept an environment input.

Before production handles real health data, add persistent managed storage, authentication, private networking, backups, data retention policy, and explicit compliance review.
