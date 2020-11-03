output "operations_container_registry_name" {
  value       = azurerm_container_registry.operations_container_registry.name
  description = "Global registry so that docker images can be reused across deployments."
}

output "operations_deployment_subnet_id" {
    value = azurerm_subnet.deployment_subnet.id
    description = "ID of the subnet all subsequent resources are deployed into."
}

output "operations_storage_account_name" {
  value       = azurerm_storage_account.operations_storage_account.name
  description = "Global storage for deployments to store their configurations and states."
}
