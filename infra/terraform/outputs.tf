output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "acr_name" {
  value = azurerm_container_registry.main.name
}

output "acr_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "key_vault_name" {
  value = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}

output "container_app_environment_default_domain" {
  value = azurerm_container_app_environment.main.default_domain
}

output "backend_container_app_name" {
  value = local.backend_app_name
}

output "frontend_container_app_name" {
  value = local.frontend_app_name
}

output "backend_url" {
  value = local.backend_url
}

output "frontend_url" {
  value = local.frontend_url
}

output "backend_api_base_url" {
  value = local.backend_api_base
}

output "azure_openai_endpoint" {
  value = local.effective_openai_endpoint
}
