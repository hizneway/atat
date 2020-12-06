

module "vpc" {
  source            = "../../modules/vpc/"
  environment       = local.environment
  region            = var.region
  virtual_network   = var.virtual_network
  networks          = var.networks
  route_tables      = var.route_tables
  owner             = var.owner
  name              = var.name
  dns_servers       = var.dns_servers
  service_endpoints = var.service_endpoints
  custom_routes     = var.routes


}





data "azurerm_resources" "aks_resources" {
  resource_group_name = module.private-k8s.k8s_resource_group_id

}


module "nsg_flow" {

  name = var.name
 location = var.location
 environment = local.environment
 vpc_name =  module.vpc.vpc_name
 resource_group_name = module.vpc.res
 security_group_ids = []
 log_workspace_id = module.logs.workspace_id
 workspace_resource_id = module.logs.workspace_resource_id

}
