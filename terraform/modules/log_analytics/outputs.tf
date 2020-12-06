output "workspace_resource_id" {
  value = azurerm_log_analytics_workspace.log_workspace.id
}

output "workspace_id" {
  value = azurerm_log_analytics_workspace.log_workspace.workspace_id
}
