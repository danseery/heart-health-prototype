#!/usr/bin/env bash
set -euo pipefail

subscription_id="${SUBSCRIPTION_ID:-ced09ae9-74a6-4f40-936f-d2eef2b577b9}"
tenant_id="${TENANT_ID:-98983dd6-f1f1-40e3-91f8-2bbf22020202}"
location="${LOCATION:-eastus2}"
repository="${REPOSITORY:-danseery/heart-health-prototype}"
environment_name="${ENVIRONMENT_NAME:-dev}"
state_resource_group_name="${STATE_RESOURCE_GROUP_NAME:-rg-heart-health-tfstate}"
state_container_name="${STATE_CONTAINER_NAME:-tfstate}"
state_key="${STATE_KEY:-heart-health-dev.tfstate}"
app_registration_name="${APP_REGISTRATION_NAME:-github-heart-health-dev}"
state_storage_account_name="${STATE_STORAGE_ACCOUNT_NAME:-}"

usage() {
  cat <<'USAGE'
Bootstrap Azure OIDC and remote Terraform state for GitHub Actions.

Environment variable overrides:
  SUBSCRIPTION_ID
  TENANT_ID
  LOCATION
  REPOSITORY
  ENVIRONMENT_NAME
  STATE_RESOURCE_GROUP_NAME
  STATE_CONTAINER_NAME
  STATE_KEY
  APP_REGISTRATION_NAME
  STATE_STORAGE_ACCOUNT_NAME
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

require_command() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "Required command '$name' was not found. Install it, then rerun this script." >&2
    exit 1
  fi
}

add_role_assignment() {
  local assignee_object_id="$1"
  local principal_type="$2"
  local role="$3"
  local scope="$4"

  local existing
  existing="$(
    az role assignment list \
      --assignee "$assignee_object_id" \
      --role "$role" \
      --scope "$scope" \
      --query '[0].id' \
      --output tsv \
      --only-show-errors
  )"

  if [[ -z "$existing" ]]; then
    az role assignment create \
      --assignee-object-id "$assignee_object_id" \
      --assignee-principal-type "$principal_type" \
      --role "$role" \
      --scope "$scope" \
      --only-show-errors >/dev/null
  fi
}

require_command az
require_command gh

if [[ -z "$state_storage_account_name" ]]; then
  suffix="$(printf '%s' "${subscription_id}-${repository}" | sha256sum | cut -c1-6)"
  state_storage_account_name="sthearttf${suffix}"
fi

echo "Using state storage account: ${state_storage_account_name}"

az account show --only-show-errors >/dev/null
az account set --subscription "$subscription_id" --only-show-errors

az group create \
  --name "$state_resource_group_name" \
  --location "$location" \
  --tags application=hearthealth-ai environment=platform managed-by=bootstrap-script \
  --only-show-errors >/dev/null

az storage account create \
  --name "$state_storage_account_name" \
  --resource-group "$state_resource_group_name" \
  --location "$location" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --only-show-errors >/dev/null

az storage account blob-service-properties update \
  --account-name "$state_storage_account_name" \
  --resource-group "$state_resource_group_name" \
  --enable-versioning true \
  --enable-delete-retention true \
  --delete-retention-days 14 \
  --enable-container-delete-retention true \
  --container-delete-retention-days 14 \
  --only-show-errors >/dev/null

current_user_object_id="$(az ad signed-in-user show --query id --output tsv --only-show-errors)"
storage_account_id="$(
  az storage account show \
    --name "$state_storage_account_name" \
    --resource-group "$state_resource_group_name" \
    --query id \
    --output tsv \
    --only-show-errors
)"

add_role_assignment "$current_user_object_id" User "Storage Blob Data Contributor" "$storage_account_id"
sleep 15

az storage container create \
  --account-name "$state_storage_account_name" \
  --name "$state_container_name" \
  --auth-mode login \
  --only-show-errors >/dev/null

existing_app_id="$(
  az ad app list \
    --display-name "$app_registration_name" \
    --query '[0].appId' \
    --output tsv \
    --only-show-errors
)"

if [[ -z "$existing_app_id" ]]; then
  app_id="$(
    az ad app create \
      --display-name "$app_registration_name" \
      --query appId \
      --output tsv \
      --only-show-errors
  )"
else
  app_id="$existing_app_id"
fi

app_object_id="$(az ad app show --id "$app_id" --query id --output tsv --only-show-errors)"

existing_sp_id="$(az ad sp show --id "$app_id" --query id --output tsv --only-show-errors 2>/dev/null || true)"
if [[ -z "$existing_sp_id" ]]; then
  sp_object_id="$(az ad sp create --id "$app_id" --query id --output tsv --only-show-errors)"
else
  sp_object_id="$existing_sp_id"
fi

credential_name="github-${environment_name}"
existing_credential="$(
  az ad app federated-credential list \
    --id "$app_object_id" \
    --query "[?name=='${credential_name}'] | [0].name" \
    --output tsv \
    --only-show-errors
)"

if [[ -z "$existing_credential" ]]; then
  credential_path="$(mktemp)"
  cat >"$credential_path" <<JSON
{
  "name": "${credential_name}",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:${repository}:environment:${environment_name}",
  "audiences": ["api://AzureADTokenExchange"],
  "description": "GitHub Actions OIDC for ${repository} ${environment_name}"
}
JSON

  az ad app federated-credential create \
    --id "$app_object_id" \
    --parameters "$credential_path" \
    --only-show-errors >/dev/null

  rm -f "$credential_path"
fi

subscription_scope="/subscriptions/${subscription_id}"
add_role_assignment "$sp_object_id" ServicePrincipal Contributor "$subscription_scope"
add_role_assignment "$sp_object_id" ServicePrincipal "User Access Administrator" "$subscription_scope"
add_role_assignment "$sp_object_id" ServicePrincipal "Storage Blob Data Contributor" "$storage_account_id"

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "repos/${repository}/environments/${environment_name}" >/dev/null

gh variable set AZURE_CLIENT_ID --repo "$repository" --env "$environment_name" --body "$app_id"
gh variable set AZURE_TENANT_ID --repo "$repository" --env "$environment_name" --body "$tenant_id"
gh variable set AZURE_SUBSCRIPTION_ID --repo "$repository" --env "$environment_name" --body "$subscription_id"
gh variable set TF_STATE_RESOURCE_GROUP_NAME --repo "$repository" --env "$environment_name" --body "$state_resource_group_name"
gh variable set TF_STATE_STORAGE_ACCOUNT_NAME --repo "$repository" --env "$environment_name" --body "$state_storage_account_name"
gh variable set TF_STATE_CONTAINER_NAME --repo "$repository" --env "$environment_name" --body "$state_container_name"
gh variable set TF_STATE_KEY --repo "$repository" --env "$environment_name" --body "$state_key"

echo
echo "Bootstrap complete."
echo "GitHub environment: ${environment_name}"
echo "Federated credential subject: repo:${repository}:environment:${environment_name}"
echo "Terraform state: ${state_resource_group_name} / ${state_storage_account_name} / ${state_container_name} / ${state_key}"
