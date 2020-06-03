


module "k8s-private" {
  source                     = "../../modules/k8s-private"
  region                     = var.region
  name                       = var.name
  environment                = var.environment
  owner                      = var.owner
  rg                         = var.private_k8s_resource_group
  service_cidr               = var.private_aks_service_cidr
  service_dns                = var.private_aks_service_dns
  docker_bridge_cidr         = var.private_aks_docker_bridge_cidr
  k8s_dns_prefix             = "private-${var.k8s_dns_prefix}"
  k8s_node_size              = var.k8s_node_size
  subnet_cidr                = var.private_k8s_subnet_cidr
  aks_ssh_pub_key_path       = var.aks_ssh_pub_key_path
  enable_auto_scaling        = true
  max_count                  = 5
  min_count                  = 3
  client_id                  = data.azurerm_key_vault_secret.k8s_client_id.value
  client_secret              = data.azurerm_key_vault_secret.k8s_client_secret.value
  client_object_id           = data.azurerm_key_vault_secret.k8s_object_id.value
  private_aks_sp_secret      = var.private_aks_sp_secret
  private_aks_sp_id          = var.private_aks_sp_id
  log_analytics_workspace_id = module.logs.workspace_id
  vnet_id                    = module.vpc.id
  vpc_name                   = module.vpc.vpc_name
}
