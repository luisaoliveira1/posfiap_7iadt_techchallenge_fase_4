locals {
  env_domain = azurerm_container_app_environment.main.default_domain
}

output "nlp_model_url" {
  value = "https://${azurerm_container_app.nlp_model.name}.${local.env_domain}"
}
output "risk_engine_url" {
  value = "https://${azurerm_container_app.risk_engine.name}.${local.env_domain}"
}
output "backend_url" {
  value = "https://${azurerm_container_app.backend.name}.${local.env_domain}"
}
output "frontend_url" {
  value = "https://${azurerm_container_app.frontend.name}.${local.env_domain}"
}
