<<<<<<< HEAD
output "container_registry_name" {
value = "${var.name}${var.environment}${var.pet_name}registry"
=======
output "name" {
  value = azurerm_container_registry.acr.name
>>>>>>> Reference dynamic container registry names
}
