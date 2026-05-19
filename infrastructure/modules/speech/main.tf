resource "azurerm_cognitive_account" "speech" {
  name                = "${var.prefix}-speech"
  resource_group_name = var.resource_group_name
  location            = var.location
  kind                = "SpeechServices"
  sku_name            = "F0"
  tags                = var.tags
}
