resource "azurerm_container_registry" "main" {
  name                = replace("${var.prefix}acr", "-", "")
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = true
  tags                = var.tags
}
