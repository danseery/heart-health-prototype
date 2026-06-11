data "azurerm_client_config" "current" {}

locals {
  normalized_resource_group_name = lower(var.resource_group_name)
  resource_group_without_prefix  = startswith(local.normalized_resource_group_name, "rg-") ? substr(local.normalized_resource_group_name, 3, length(local.normalized_resource_group_name) - 3) : local.normalized_resource_group_name
  name_slug_compacted            = replace(replace(local.resource_group_without_prefix, "/[^a-z0-9-]/", "-"), "/-+/", "-")
  name_slug                      = trim(local.name_slug_compacted, "-")
  name_token                     = replace(local.name_slug, "-", "")
  hyphen_suffix                  = var.global_name_suffix == "" ? "" : "-${var.global_name_suffix}"
  compact_suffix                 = var.global_name_suffix == "" ? "" : var.global_name_suffix

  acr_name       = var.container_registry_name == "" ? substr("acr${local.name_token}${local.compact_suffix}", 0, 50) : var.container_registry_name
  key_vault_name = var.key_vault_name == "" ? substr("kv-${local.name_slug}${local.hyphen_suffix}", 0, 24) : var.key_vault_name

  log_analytics_name         = "log-${local.name_slug}"
  app_insights_name          = "appi-${local.name_slug}"
  container_environment_name = "cae-${local.name_slug}"
  app_identity_name          = "id-${local.name_slug}-apps"
  backend_app_name           = "ca-${local.name_slug}-api"
  frontend_app_name          = "ca-${local.name_slug}-web"
  openai_account_name        = var.azure_openai_account_name == "" ? substr("oai-${local.name_slug}${local.hyphen_suffix}", 0, 64) : var.azure_openai_account_name

  backend_url               = "https://${local.backend_app_name}.${azurerm_container_app_environment.main.default_domain}"
  frontend_url              = "https://${local.frontend_app_name}.${azurerm_container_app_environment.main.default_domain}"
  backend_api_base          = "${local.backend_url}/api"
  effective_openai_endpoint = var.create_azure_openai_resource ? azurerm_cognitive_account.openai[0].endpoint : var.azure_openai_endpoint
  common_tags = merge(var.tags, {
    application  = "hearthealth-ai"
    environment  = var.environment
    "managed-by" = "terraform"
  })
}

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.common_tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = local.log_analytics_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days
  tags                = local.common_tags
}

resource "azurerm_application_insights" "main" {
  name                = local.app_insights_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = local.common_tags
}

resource "azurerm_container_registry" "main" {
  name                          = local.acr_name
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  sku                           = "Basic"
  admin_enabled                 = false
  public_network_access_enabled = true
  tags                          = local.common_tags
}

resource "azurerm_key_vault" "main" {
  name                          = local.key_vault_name
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  tenant_id                     = var.tenant_id
  sku_name                      = "standard"
  rbac_authorization_enabled    = true
  purge_protection_enabled      = var.key_vault_purge_protection_enabled
  public_network_access_enabled = true
  soft_delete_retention_days    = 7
  tags                          = local.common_tags
}

resource "azurerm_user_assigned_identity" "apps" {
  name                = local.app_identity_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.common_tags
}

resource "azurerm_cognitive_account" "openai" {
  count                         = var.create_azure_openai_resource ? 1 : 0
  name                          = local.openai_account_name
  location                      = azurerm_resource_group.main.location
  resource_group_name           = azurerm_resource_group.main.name
  kind                          = "OpenAI"
  sku_name                      = "S0"
  custom_subdomain_name         = local.openai_account_name
  public_network_access_enabled = true
  tags                          = local.common_tags
}

resource "azurerm_role_assignment" "apps_acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.apps.principal_id
}

resource "azurerm_role_assignment" "apps_key_vault_secrets_user" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.apps.principal_id
}

resource "azurerm_role_assignment" "deployer_key_vault_admin" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "apps_openai_user" {
  count                = var.create_azure_openai_resource ? 1 : 0
  scope                = azurerm_cognitive_account.openai[0].id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_user_assigned_identity.apps.principal_id
}

resource "azurerm_container_app_environment" "main" {
  name                       = local.container_environment_name
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = local.common_tags
}

resource "azurerm_container_app" "backend" {
  count                        = var.create_container_apps ? 1 : 0
  name                         = local.backend_app_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.common_tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.apps.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.apps.id
  }

  secret {
    name  = "azure-openai-api-key"
    value = var.azure_openai_api_key
  }

  ingress {
    external_enabled           = true
    allow_insecure_connections = false
    target_port                = 8000
    transport                  = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0
    max_replicas = 2

    container {
      name   = "api"
      image  = "${azurerm_container_registry.main.login_server}/${var.backend_image_name}:${var.container_image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "APP_ENV"
        value = var.environment
      }

      env {
        name  = "APP_NAME"
        value = "HeartHealth AI"
      }

      env {
        name  = "FRONTEND_ORIGINS"
        value = local.frontend_url
      }

      env {
        name  = "DATABASE_URL"
        value = "sqlite:///./local_data/hearthealth_dev.db"
      }

      env {
        name  = "AI_PROVIDER"
        value = var.ai_provider
      }

      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = local.effective_openai_endpoint
      }

      env {
        name  = "AZURE_OPENAI_DEPLOYMENT"
        value = var.azure_openai_deployment
      }

      env {
        name  = "AZURE_OPENAI_API_VERSION"
        value = var.azure_openai_api_version
      }

      env {
        name        = "AZURE_OPENAI_API_KEY"
        secret_name = "azure-openai-api-key"
      }

      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.main.connection_string
      }
    }
  }
}

resource "azurerm_container_app" "frontend" {
  count                        = var.create_container_apps ? 1 : 0
  name                         = local.frontend_app_name
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.common_tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.apps.id]
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.apps.id
  }

  ingress {
    external_enabled           = true
    allow_insecure_connections = false
    target_port                = 8080
    transport                  = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0
    max_replicas = 2

    container {
      name   = "web"
      image  = "${azurerm_container_registry.main.login_server}/${var.frontend_image_name}:${var.container_image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }
}
