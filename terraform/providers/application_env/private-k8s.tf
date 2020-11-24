module "private-k8s" {
  source                     = "../../modules/k8s-private"
  rg                         = module.vpc.resource_group_name
  region                     = var.region
  name                       = var.name
  environment                = local.environment
  owner                      = var.owner
  k8s_dns_prefix             = var.k8s_dns_prefix
  k8s_node_size              = "Standard_D2_v3"
  enable_auto_scaling        = true
  max_count                  = 3
  min_count                  = 3
  private_aks_sp_id          = var.private_aks_sp_id
  private_aks_sp_secret      = var.private_aks_sp_secret
  log_analytics_workspace_id = module.logs.workspace_id
  service_dns                = var.private_aks_service_dns
  docker_bridge_cidr         = var.private_aks_docker_bridge_cidr
  service_cidr               = var.private_aks_service_cidr
  subnet_cidr                = var.private_k8s_subnet_cidr
  vnet_id                    = module.vpc.id
  vpc_name                   = module.vpc.vpc_name
  aks_ssh_pub_key_path       = var.aks_ssh_pub_key_path
  aks_subnet_id              = module.vpc.subnet_list["aks-private"].id
  vpc_address_space          = "10.1.0.0/16"
  subnet_name         = element(split(",",var.networks["aks-private"]),1)
  depends_on = [module.vpc, module.keyvault_reader_identity,module.private-aks-firewall.rt_association_id]


}





module "private-aks-firewall" {

  source              = "../../modules/azure_firewall"
  resource_group_name = module.vpc.resource_group_name
  location            = var.region
  name                = var.name
  environment         = local.environment
  subnet_id           = module.vpc.subnet_list["AzureFirewallSubnet"].id
  az_fw_ip            = module.vpc.fw_ip_address
  az_fw_ip_id         = module.vpc.fw_ip_address_id
  maintenance_page_ip = "10.1.5.199"
  nat_rules_translated_ips  = cidrhost("${var.private_k8s_subnet_cidr}",201)
  virtual_appliance_routes       = var.virtual_appliance_routes
  virtual_appliance_route_tables = var.virtual_appliance_route_tables
  vnet_cidr           = var.virtual_network
  subnets             = module.vpc.subnet_list
  depends_on = [module.vpc.subnet_list]

}
