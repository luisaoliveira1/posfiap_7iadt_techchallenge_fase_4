resource "azurerm_cognitive_account" "language" {
  name                = "${var.prefix}-language"
  resource_group_name = var.resource_group_name
  location            = var.location
  kind                = "TextAnalytics"
  sku_name            = "F0"
  tags                = var.tags
}
