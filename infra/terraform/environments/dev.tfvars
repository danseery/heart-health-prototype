resource_group_name = "rg-heart-health-dev"
location            = "eastus2"
environment         = "dev"

ai_provider                  = "azure_openai"
create_azure_openai_resource = false
azure_openai_endpoint        = "https://big-brain.openai.azure.com/"
azure_openai_deployment      = ""

tags = {
  "cost-center" = "side-projects"
  "data-class"  = "prototype-sensitive"
}
