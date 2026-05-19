# System topic scoped to the storage account
resource "azurerm_eventgrid_system_topic" "storage" {
  name                   = "${var.prefix}-evgt-storage"
  resource_group_name    = var.resource_group_name
  location               = var.location
  source_arm_resource_id = var.storage_account_id
  topic_type             = "Microsoft.Storage.StorageAccounts"
  tags                   = var.tags
}

# Subscription 1: audio-uploads BlobCreated → process_audio function
resource "azurerm_eventgrid_system_topic_event_subscription" "process_audio" {
  name                = "${var.prefix}-sub-process-audio"
  system_topic        = azurerm_eventgrid_system_topic.storage.name
  resource_group_name = var.resource_group_name

  included_event_types = ["Microsoft.Storage.BlobCreated"]

  subject_filter {
    subject_begins_with = "/blobServices/default/containers/audio-uploads/"
  }

  azure_function_endpoint {
    function_id = "${var.function_app_id}/functions/process_audio"
  }
}

# Subscription 2: labeled-data BlobCreated → trigger_retrain function
resource "azurerm_eventgrid_system_topic_event_subscription" "trigger_retrain" {
  name                = "${var.prefix}-sub-trigger-retrain"
  system_topic        = azurerm_eventgrid_system_topic.storage.name
  resource_group_name = var.resource_group_name

  included_event_types = ["Microsoft.Storage.BlobCreated"]

  subject_filter {
    subject_begins_with = "/blobServices/default/containers/labeled-data/"
    subject_ends_with   = ".csv"
  }

  azure_function_endpoint {
    function_id = "${var.function_app_id}/functions/trigger_retrain"
  }
}

# Subscription 3: transcripts BlobCreated → analyze_transcript function
resource "azurerm_eventgrid_system_topic_event_subscription" "analyze_transcript" {
  name                = "${var.prefix}-sub-analyze-transcript"
  system_topic        = azurerm_eventgrid_system_topic.storage.name
  resource_group_name = var.resource_group_name

  included_event_types = ["Microsoft.Storage.BlobCreated"]

  subject_filter {
    subject_begins_with = "/blobServices/default/containers/transcripts/"
    subject_ends_with   = ".json"
  }

  azure_function_endpoint {
    function_id = "${var.function_app_id}/functions/analyze_transcript"
  }
}
