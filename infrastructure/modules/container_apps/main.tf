resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.prefix}-law-ca"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_container_app_environment" "main" {
  name                       = "${var.prefix}-cae"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = var.tags
}

# ── NLP model ──────────────────────────────────────────────────────────────────
# External so both the backend container and Azure Functions can reach it.
resource "azurerm_container_app" "nlp_model" {
  name                         = "${var.prefix}-nlp-model"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  secret {
    name  = "acr-password"
    value = var.acr_admin_password
  }
  secret {
    name  = "azure-blob-conn-str"
    value = var.azure_blob_connection_string
  }
  secret {
    name  = "retrain-secret"
    value = var.retrain_secret
  }

  registry {
    server               = var.acr_login_server
    username             = var.acr_admin_username
    password_secret_name = "acr-password"
  }

  ingress {
    external_enabled = true
    target_port      = 8001
    transport        = "http"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 0
    max_replicas = 3
    container {
      name   = "nlp-model"
      image  = "${var.acr_login_server}/nlp-model:latest"
      cpu    = 1.0
      memory = "2Gi"

      env {
        name        = "AZURE_BLOB_CONNECTION_STRING"
        secret_name = "azure-blob-conn-str"
      }
      env {
        name  = "MODELS_BLOB_CONTAINER"
        value = "models"
      }
      env {
        name  = "TRAINING_DATA_CONTAINER"
        value = "training-data"
      }
      env {
        name        = "RETRAIN_SECRET"
        secret_name = "retrain-secret"
      }
      env {
        name  = "RISK_ENGINE_URL"
        value = "https://${azurerm_container_app.risk_engine.name}.${azurerm_container_app_environment.main.default_domain}"
      }
    }
  }
}

# ── Risk engine ────────────────────────────────────────────────────────────────
resource "azurerm_container_app" "risk_engine" {
  name                         = "${var.prefix}-risk-engine"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  secret {
    name  = "acr-password"
    value = var.acr_admin_password
  }
  secret {
    name  = "azure-blob-conn-str"
    value = var.azure_blob_connection_string
  }
  secret {
    name  = "retrain-secret"
    value = var.retrain_secret
  }

  registry {
    server               = var.acr_login_server
    username             = var.acr_admin_username
    password_secret_name = "acr-password"
  }

  ingress {
    external_enabled = true
    target_port      = 8002
    transport        = "http"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 0
    max_replicas = 3
    container {
      name   = "risk-engine"
      image  = "${var.acr_login_server}/risk-engine:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name        = "AZURE_BLOB_CONNECTION_STRING"
        secret_name = "azure-blob-conn-str"
      }
      env {
        name  = "MODELS_BLOB_CONTAINER"
        value = "models"
      }
      env {
        name  = "TRAINING_DATA_CONTAINER"
        value = "training-data"
      }
      env {
        name        = "RETRAIN_SECRET"
        secret_name = "retrain-secret"
      }
    }
  }
}

# ── Backend orchestrator ───────────────────────────────────────────────────────
resource "azurerm_container_app" "backend" {
  name                         = "${var.prefix}-backend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  secret {
    name  = "acr-password"
    value = var.acr_admin_password
  }
  secret {
    name  = "azure-speech-key"
    value = var.azure_speech_key
  }
  secret {
    name  = "azure-blob-conn-str"
    value = var.azure_blob_connection_string
  }

  registry {
    server               = var.acr_login_server
    username             = var.acr_admin_username
    password_secret_name = "acr-password"
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "http"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 0
    max_replicas = 5
    container {
      name   = "backend"
      image  = "${var.acr_login_server}/backend:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name        = "AZURE_SPEECH_KEY"
        secret_name = "azure-speech-key"
      }
      env {
        name  = "AZURE_SPEECH_REGION"
        value = var.azure_speech_region
      }
      env {
        name        = "AZURE_BLOB_CONNECTION_STRING"
        secret_name = "azure-blob-conn-str"
      }
      env {
        name  = "NLP_MODEL_URL"
        value = "https://${azurerm_container_app.nlp_model.name}.${azurerm_container_app_environment.main.default_domain}"
      }
      env {
        name  = "RISK_ENGINE_URL"
        value = "https://${azurerm_container_app.risk_engine.name}.${azurerm_container_app_environment.main.default_domain}"
      }
      env {
        name  = "STT_BACKEND"
        value = "azure"
      }
    }
  }
}

# ── Frontend ───────────────────────────────────────────────────────────────────
resource "azurerm_container_app" "frontend" {
  name                         = "${var.prefix}-frontend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"
  tags                         = var.tags

  secret {
    name  = "acr-password"
    value = var.acr_admin_password
  }

  registry {
    server               = var.acr_login_server
    username             = var.acr_admin_username
    password_secret_name = "acr-password"
  }

  ingress {
    external_enabled = true
    target_port      = 80
    transport        = "http"
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  template {
    min_replicas = 0
    max_replicas = 5
    container {
      name   = "frontend"
      image  = "${var.acr_login_server}/frontend:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      # nginx template substitution: replaces ${BACKEND_URL} in nginx.conf at container start
      env {
        name  = "BACKEND_URL"
        value = "https://${azurerm_container_app.backend.name}.${azurerm_container_app_environment.main.default_domain}"
      }
    }
  }
}
