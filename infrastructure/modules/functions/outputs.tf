output "function_app_id" {
  value = azurerm_linux_function_app.main.id
}
output "function_app_name" {
  value = azurerm_linux_function_app.main.name
}
output "app_hostname" {
  value = azurerm_linux_function_app.main.default_hostname
}
