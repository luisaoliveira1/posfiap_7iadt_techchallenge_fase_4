output "key" {
  value     = azurerm_cognitive_account.speech.primary_access_key
  sensitive = true
}
output "endpoint" { value = azurerm_cognitive_account.speech.endpoint }
