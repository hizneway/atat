resource "azurerm_resource_group" "redis" {
  name     = "${var.name}-redis-${var.deployment_namespace}"
  location = var.deployment_location
}

# NOTE: the Name used for Redis needs to be globally unique
resource "azurerm_redis_cache" "redis" {
  name                = "${var.name}-redis-${var.deployment_namespace}"
  location            = azurerm_resource_group.redis.location
  resource_group_name = azurerm_resource_group.redis.name
  capacity            = 1
  family              = "P"
  sku_name            = "Premium"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
  subnet_id           = module.vpc.redis_subnet_id

  redis_configuration {
    enable_authentication = true
  }
  tags = {
    environment = var.deployment_namespace
    owner       = var.owner
  }
}
