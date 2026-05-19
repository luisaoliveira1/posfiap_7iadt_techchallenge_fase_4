resource "azurerm_service_plan" "main" {
  name                = "${var.prefix}-asp"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1"  # Consumption plan
  tags                = var.tags
}

resource "azurerm_application_insights" "main" {
  name                = "${var.prefix}-appinsights"
  resource_group_name = var.resource_group_name
  location            = var.location
  application_type    = "other"
  tags                = var.tags

  lifecycle {
    ignore_changes = [workspace_id]
  }
}

resource "azurerm_linux_function_app" "main" {
  name                       = "${var.prefix}-func"
  resource_group_name        = var.resource_group_name
  location                   = var.location
  service_plan_id            = azurerm_service_plan.main.id
  storage_account_name       = var.storage_account_name
  storage_account_access_key = var.storage_account_access_key

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME              = "python"
    APPINSIGHTS_INSTRUMENTATIONKEY        = azurerm_application_insights.main.instrumentation_key
    AZURE_SPEECH_KEY                      = var.speech_key
    AZURE_SPEECH_REGION                   = var.speech_region
    AZURE_STORAGE_CONNECTION_STRING       = var.storage_connection_string
    NLP_MODEL_URL                         = var.nlp_model_url
    RISK_ENGINE_URL                       = var.risk_engine_url
    RETRAIN_SECRET                        = var.retrain_secret
  }

  tags = var.tags
}
