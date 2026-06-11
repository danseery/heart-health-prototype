variable "subscription_id" {
  description = "Azure subscription ID used for this environment."
  type        = string
}

variable "tenant_id" {
  description = "Azure tenant ID used for this environment."
  type        = string
}

variable "resource_group_name" {
  description = "Environment resource group. Resource names are derived from this value."
  type        = string
}

variable "location" {
  description = "Azure region for environment resources."
  type        = string
}

variable "environment" {
  description = "Short environment name, such as dev or prod."
  type        = string
}

variable "global_name_suffix" {
  description = "Optional deterministic suffix for globally unique names such as ACR and Key Vault."
  type        = string
  default     = ""
}

variable "container_registry_name" {
  description = "Optional override for the Azure Container Registry name."
  type        = string
  default     = ""
}

variable "key_vault_name" {
  description = "Optional override for the Azure Key Vault name."
  type        = string
  default     = ""
}

variable "container_image_tag" {
  description = "Container image tag deployed to Azure Container Apps."
  type        = string
  default     = "bootstrap"
}

variable "create_container_apps" {
  description = "Set false during the first deploy phase so ACR can be created before images are pushed."
  type        = bool
  default     = true
}

variable "backend_image_name" {
  description = "Backend image repository name in ACR."
  type        = string
  default     = "hearthealth-api"
}

variable "frontend_image_name" {
  description = "Frontend image repository name in ACR."
  type        = string
  default     = "hearthealth-web"
}

variable "ai_provider" {
  description = "AI provider configured for the backend."
  type        = string
  default     = "azure_openai"
}

variable "create_azure_openai_resource" {
  description = "Create an Azure OpenAI account in this environment resource group instead of using azure_openai_endpoint."
  type        = bool
  default     = false
}

variable "azure_openai_account_name" {
  description = "Optional override for the Azure OpenAI account name when create_azure_openai_resource is true."
  type        = string
  default     = ""
}

variable "azure_openai_endpoint" {
  description = "Azure OpenAI or Azure AI Foundry endpoint. This is not a secret."
  type        = string
  default     = ""
}

variable "azure_openai_deployment" {
  description = "Azure OpenAI model deployment name used by the application when implemented."
  type        = string
  default     = ""
}

variable "azure_openai_api_key" {
  description = "Azure OpenAI or Azure AI Foundry API key used by the backend. Prefer managed identity before production."
  type        = string
  default     = ""
  sensitive   = true
}

variable "azure_openai_api_version" {
  description = "Azure OpenAI API version used by the application when implemented."
  type        = string
  default     = "2024-10-21"
}

variable "log_retention_days" {
  description = "Log Analytics retention period."
  type        = number
  default     = 30
}

variable "key_vault_purge_protection_enabled" {
  description = "Enable purge protection. Recommended for production; optional for disposable dev environments."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags applied to resources."
  type        = map(string)
  default     = {}
}
