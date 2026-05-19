locals {
  project  = var.project
  env      = var.environment
  location = var.location
  prefix   = "${var.project}-${var.environment}"
  tags = {
    project     = "posfiap-ppd"
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "random_password" "retrain_secret" {
  length  = 32
  special = false
}

resource "azurerm_resource_group" "main" {
  name     = "${local.prefix}-rg"
  location = local.location
  tags     = local.tags
}

module "storage" {
  source              = "./modules/storage"
  resource_group_name = azurerm_resource_group.main.name
  location            = local.location
  prefix              = local.prefix
  tags                = local.tags
}

module "speech" {
  source              = "./modules/speech"
  resource_group_name = azurerm_resource_group.main.name
  location            = local.location
  prefix              = local.prefix
  tags                = local.tags
}

module "language" {
  source              = "./modules/language"
  resource_group_name = azurerm_resource_group.main.name
  location            = local.location
  prefix              = local.prefix
  tags                = local.tags
}

module "container_registry" {
  source              = "./modules/container_registry"
  resource_group_name = azurerm_resource_group.main.name
  location            = local.location
  prefix              = local.prefix
  tags                = local.tags
}

module "container_apps" {
  source                       = "./modules/container_apps"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = local.location
  prefix                       = local.prefix
  acr_login_server             = module.container_registry.login_server
  acr_admin_username           = module.container_registry.admin_username
  acr_admin_password           = module.container_registry.admin_password
  azure_speech_key             = module.speech.key
  azure_speech_region          = local.location
  azure_blob_connection_string = module.storage.connection_string
  retrain_secret               = random_password.retrain_secret.result
  tags                         = local.tags
}

module "functions" {
  source                     = "./modules/functions"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = local.location
  prefix                     = local.prefix
  storage_account_name       = module.storage.account_name
  storage_account_access_key = module.storage.primary_access_key
  storage_connection_string  = module.storage.connection_string
  speech_key                 = module.speech.key
  speech_region              = local.location
  nlp_model_url              = module.container_apps.nlp_model_url
  risk_engine_url            = module.container_apps.risk_engine_url
  retrain_secret             = random_password.retrain_secret.result
  tags                       = local.tags
}

module "event_grid" {
  source              = "./modules/event_grid"
  resource_group_name = azurerm_resource_group.main.name
  location            = local.location
  prefix              = local.prefix
  storage_account_id  = module.storage.account_id
  function_app_id     = module.functions.function_app_id
  tags                = local.tags
}

module "ai_foundry" {
  source              = "./modules/ai_foundry"
  resource_group_name = azurerm_resource_group.main.name
  location            = local.location
  prefix              = local.prefix
  storage_account_id  = module.storage.account_id
  tags                = local.tags
}
