

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






module "nsg_flow" {

  source = "../../modules/nsg_flowlogs"

  name                  = var.name
  location              = var.region
  environment           = local.environment
  vpc_name              = module.vpc.vpc_name
  resource_group_name   = module.vpc.resource_group_name
  security_group_id    = module.vpc.logging_nsg_id
  log_workspace_id      = module.logs.workspace_id
  workspace_resource_id = module.logs.workspace_resource_id

}
