


module "maintenancepage" {

 source = "../../modules/maintenance_page"
 name = var.name
 environment = locals.environment
 resource_group = var.resource_group
 location = var.location
 ops_container_registry = "${var.name}opsregistry.azurecr.io"
 nginx_container_image =  "maintenacepage:latest"
 registry_username = "${var.name}opsregistry"
 registry_password = var.ops_container_registry_pass


}
