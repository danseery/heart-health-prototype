[CmdletBinding()]
param(
    [string]$SubscriptionId = "ced09ae9-74a6-4f40-936f-d2eef2b577b9",
    [string]$TenantId = "98983dd6-f1f1-40e3-91f8-2bbf22020202",
    [string]$Location = "eastus2",
    [string]$Repository = "danseery/heart-health-prototype",
    [string]$EnvironmentName = "dev",
    [string]$StateResourceGroupName = "rg-heart-health-tfstate",
    [string]$StateContainerName = "tfstate",
    [string]$StateKey = "heart-health-dev.tfstate",
    [string]$AppRegistrationName = "github-heart-health-dev",
    [string]$StateStorageAccountName = ""
)

$ErrorActionPreference = "Stop"

function Assert-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found. Install it, then rerun this script."
    }
}

function New-StorageSuffix {
    param([string]$Seed)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Seed)
    $hash = $sha.ComputeHash($bytes)
    return -join ($hash[0..2] | ForEach-Object { $_.ToString("x2") })
}

function Add-RoleAssignment {
    param(
        [string]$AssigneeObjectId,
        [string]$PrincipalType,
        [string]$Role,
        [string]$Scope
    )

    $existing = az role assignment list `
        --assignee $AssigneeObjectId `
        --role $Role `
        --scope $Scope `
        --query "[0].id" `
        --output tsv `
        --only-show-errors

    if ([string]::IsNullOrWhiteSpace($existing)) {
        az role assignment create `
            --assignee-object-id $AssigneeObjectId `
            --assignee-principal-type $PrincipalType `
            --role $Role `
            --scope $Scope `
            --only-show-errors 1>$null
    }
}

Assert-Command az
Assert-Command gh

if ([string]::IsNullOrWhiteSpace($StateStorageAccountName)) {
    $suffix = New-StorageSuffix "$SubscriptionId-$Repository"
    $StateStorageAccountName = "sthearttf$suffix"
}

Write-Host "Using state storage account: $StateStorageAccountName"

az account show --only-show-errors 1>$null
az account set --subscription $SubscriptionId --only-show-errors

az group create `
    --name $StateResourceGroupName `
    --location $Location `
    --tags application=hearthealth-ai environment=platform managed-by=bootstrap-script `
    --only-show-errors 1>$null

az storage account create `
    --name $StateStorageAccountName `
    --resource-group $StateResourceGroupName `
    --location $Location `
    --sku Standard_LRS `
    --kind StorageV2 `
    --min-tls-version TLS1_2 `
    --allow-blob-public-access false `
    --only-show-errors 1>$null

az storage account blob-service-properties update `
    --account-name $StateStorageAccountName `
    --resource-group $StateResourceGroupName `
    --enable-versioning true `
    --enable-delete-retention true `
    --delete-retention-days 14 `
    --enable-container-delete-retention true `
    --container-delete-retention-days 14 `
    --only-show-errors 1>$null

$currentUserObjectId = az ad signed-in-user show --query id --output tsv --only-show-errors
$storageAccountId = az storage account show `
    --name $StateStorageAccountName `
    --resource-group $StateResourceGroupName `
    --query id `
    --output tsv `
    --only-show-errors

Add-RoleAssignment `
    -AssigneeObjectId $currentUserObjectId `
    -PrincipalType User `
    -Role "Storage Blob Data Contributor" `
    -Scope $storageAccountId

Start-Sleep -Seconds 15

az storage container create `
    --account-name $StateStorageAccountName `
    --name $StateContainerName `
    --auth-mode login `
    --only-show-errors 1>$null

$existingAppId = az ad app list `
    --display-name $AppRegistrationName `
    --query "[0].appId" `
    --output tsv `
    --only-show-errors

if ([string]::IsNullOrWhiteSpace($existingAppId)) {
    $appId = az ad app create `
        --display-name $AppRegistrationName `
        --query appId `
        --output tsv `
        --only-show-errors
} else {
    $appId = $existingAppId
}

$appObjectId = az ad app show --id $appId --query id --output tsv --only-show-errors

$existingSpId = az ad sp list `
    --filter "appId eq '$appId'" `
    --query "[0].id" `
    --output tsv `
    --only-show-errors
if ([string]::IsNullOrWhiteSpace($existingSpId)) {
    $spObjectId = az ad sp create --id $appId --query id --output tsv --only-show-errors
} else {
    $spObjectId = $existingSpId
}

$credentialName = "github-$EnvironmentName"
$existingCredential = az ad app federated-credential list `
    --id $appObjectId `
    --query "[?name=='$credentialName'] | [0].name" `
    --output tsv `
    --only-show-errors

if ([string]::IsNullOrWhiteSpace($existingCredential)) {
    $credential = @{
        name        = $credentialName
        issuer      = "https://token.actions.githubusercontent.com"
        subject     = "repo:${Repository}:environment:${EnvironmentName}"
        audiences   = @("api://AzureADTokenExchange")
        description = "GitHub Actions OIDC for $Repository $EnvironmentName"
    } | ConvertTo-Json -Depth 5

    $credentialPath = Join-Path ([System.IO.Path]::GetTempPath()) "github-oidc-$EnvironmentName.json"
    Set-Content -Path $credentialPath -Value $credential -Encoding utf8

    az ad app federated-credential create `
        --id $appObjectId `
        --parameters $credentialPath `
        --only-show-errors 1>$null

    Remove-Item -Path $credentialPath -Force
}

$subscriptionScope = "/subscriptions/$SubscriptionId"
Add-RoleAssignment `
    -AssigneeObjectId $spObjectId `
    -PrincipalType ServicePrincipal `
    -Role Contributor `
    -Scope $subscriptionScope

Add-RoleAssignment `
    -AssigneeObjectId $spObjectId `
    -PrincipalType ServicePrincipal `
    -Role "User Access Administrator" `
    -Scope $subscriptionScope

Add-RoleAssignment `
    -AssigneeObjectId $spObjectId `
    -PrincipalType ServicePrincipal `
    -Role "Storage Blob Data Contributor" `
    -Scope $storageAccountId

gh api `
    --method PUT `
    -H "Accept: application/vnd.github+json" `
    "repos/$Repository/environments/$EnvironmentName" 1>$null

gh variable set AZURE_CLIENT_ID --repo $Repository --env $EnvironmentName --body $appId
gh variable set AZURE_TENANT_ID --repo $Repository --env $EnvironmentName --body $TenantId
gh variable set AZURE_SUBSCRIPTION_ID --repo $Repository --env $EnvironmentName --body $SubscriptionId
gh variable set TF_STATE_RESOURCE_GROUP_NAME --repo $Repository --env $EnvironmentName --body $StateResourceGroupName
gh variable set TF_STATE_STORAGE_ACCOUNT_NAME --repo $Repository --env $EnvironmentName --body $StateStorageAccountName
gh variable set TF_STATE_CONTAINER_NAME --repo $Repository --env $EnvironmentName --body $StateContainerName
gh variable set TF_STATE_KEY --repo $Repository --env $EnvironmentName --body $StateKey

Write-Host ""
Write-Host "Bootstrap complete."
Write-Host "GitHub environment: $EnvironmentName"
Write-Host "Federated credential subject: repo:${Repository}:environment:${EnvironmentName}"
Write-Host "Terraform state: $StateResourceGroupName / $StateStorageAccountName / $StateContainerName / $StateKey"
