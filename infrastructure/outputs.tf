output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "function_app_name" {
  value = module.functions.function_app_name
}

output "speech_key" {
  value     = module.speech.key
  sensitive = true
}

output "speech_region" {
  value = var.location
}

output "storage_connection_string" {
  value     = module.storage.connection_string
  sensitive = true
}

output "container_registry_login_server" {
  value = module.container_registry.login_server
}

output "ai_foundry_workspace_url" {
  value = module.ai_foundry.workspace_url
}

output "frontend_url" {
  value = module.container_apps.frontend_url
}

output "backend_url" {
  value = module.container_apps.backend_url
}
