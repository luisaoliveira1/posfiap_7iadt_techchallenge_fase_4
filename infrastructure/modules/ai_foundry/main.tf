resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_key_vault" "foundry" {
  name                = "${var.prefix}-kv-${random_string.suffix.result}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
  tags                = var.tags
}

resource "azurerm_application_insights" "foundry" {
  name                = "${var.prefix}-ai-insights"
  resource_group_name = var.resource_group_name
  location            = var.location
  application_type    = "web"
  tags                = var.tags

  lifecycle {
    ignore_changes = [workspace_id]
  }
}

# Azure Machine Learning Workspace (AI Foundry hub)
resource "azurerm_machine_learning_workspace" "foundry" {
  name                          = "${var.prefix}-foundry"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  application_insights_id       = azurerm_application_insights.foundry.id
  key_vault_id                  = azurerm_key_vault.foundry.id
  storage_account_id            = var.storage_account_id
  public_network_access_enabled = true

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

data "azurerm_client_config" "current" {}
