output "key" {
  value     = azurerm_cognitive_account.language.primary_access_key
  sensitive = true
}
output "endpoint" { value = azurerm_cognitive_account.language.endpoint }
