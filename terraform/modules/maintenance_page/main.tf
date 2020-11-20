

resource "azurerm_network_profile" "maintenance_page" {
  name                = "maintenance_page"
  location            = var.location
  resource_group_name = var.resource_group

  container_network_interface {
    name = "maintenancepagenic"

    ip_configuration {
      name      = "maintenancepageip"
      subnet_id = var.subnet_id
    }
  }
}



resource "azurerm_container_group" "nginx_maintenance_page" {
  name                = "${var.name}-maintenance-page-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group
  ip_address_type     = "private"
  network_profile_id  = azurerm_network_profile.maintenance_page.id
  os_type             = "Linux"

  container {
    name     = "maintenance_page"
    image    = "${var.ops_container_registry}/${var.nginx_container_image}"
    cpu      = "1"
    memory   = "2"
    commands = ["nginx", "-g", "daemon off;"]

    ports {
      port     = 443
      protocol = "TCP"
    }
  }

  image_registry_credential {

    username = var.registry_username
    password = var.registry_password
    server   = var.ops_container_registry

  }




  tags = {
    environment = var.environment
  }
}
