output "workspace_url" {
  value = "https://ml.azure.com/workspaces/${azurerm_machine_learning_workspace.foundry.name}"
}
output "workspace_id" {
  value = azurerm_machine_learning_workspace.foundry.id
}
