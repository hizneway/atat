
resource "azurerm_network_watcher" "vpc" {
  name                = "${var.name}-network-watcher-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
}



resource "azurerm_storage_account" "flowlogs_storage" {
  name                     = "nsgflowlogs"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier              = "Standard"
  account_kind              = "StorageV2"
  account_replication_type  = "LRS"
  enable_https_traffic_only = true

}




resource "azurerm_network_watcher_flow_log" "vpc" {

  for_each             = var.security_group_ids
  network_watcher_name = var.vpc_name
  resource_group_name  = var.resource_group_name

  network_security_group_id = each.value
  storage_account_id        = azurerm_storage_account.flowlogs_storage.id
  enabled                   = true

  retention_policy {
    enabled = true
    days    = 7
  }

  traffic_analytics {
    enabled               = true
    workspace_id          = var.log_workspace_id
    workspace_region      = var.location
    workspace_resource_id = var.workspace_id
    interval_in_minutes   = 10
  }
}
