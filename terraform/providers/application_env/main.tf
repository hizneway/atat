data "http" "myip" {
  url = "http://ipinfo.io/ip"
}

data "azurerm_client_config" "current" {}

data "azurerm_client_config" "azure_client" { }

locals {
  deployment_subnet_id            = data.terraform_remote_state.previous_stage.outputs.operations_deployment_subnet_id
  operations_container_registry   = data.terraform_remote_state.previous_stage.outputs.operations_container_registry_login_server
  operations_resource_group_name  = data.terraform_remote_state.previous_stage.outputs.operations_resource_group_name
  operations_storage_account_name = data.terraform_remote_state.previous_stage.outputs.operations_storage_account_name
  operator_ip                     = chomp(data.http.myip.body)
  log_analytics_workspace_id      = data.terraform_remote_state.previous_stage.outputs.logging_workspace_id
}

module "tenant_keyvault_app" {
  source = "../../modules/azure_ad"
  name   = "tenant-keyvault"
  deployment_namespace = var.deployment_namespace
}

# Task order bucket is required to be accessible publicly by the users.
# which is why the policy here is "Allow"
module "task_order_bucket" {
  source                 = "../../modules/bucket"
  service_name           = "${var.deployment_namespace}tasks"
  owner                  = var.owner
  name                   = var.name
  environment            = var.deployment_namespace
  region                 = var.deployment_location
  policy                 = "Allow"
  subnet_ids             = [azurerm_subnet.aks.id]
  whitelist              = { "operator" = local.operator_ip }
  bucket_cors_properties = var.bucket_cors_properties
  storage_container_name = var.task_order_bucket_storage_container_name
  # depends_on             = [module.vpc]
}

module "container_registry" {
  source        = "../../modules/container_registry"
  name          = var.name
  region        = var.deployment_location
  environment   = var.deployment_namespace
  owner         = var.owner
  backup_region = "" # TODO(jesse) Unused.
  policy        = "Allow"
  whitelist     = { "operator" = local.operator_ip }
  workspace_id  = local.log_analytics_workspace_id
  subnet_list   = [
    azurerm_subnet.aks.id,
    azurerm_subnet.edge.id,
    azurerm_subnet.mgmt_subnet.id,
  ]
  # depends_on    = [module.vpc]
  # ops_container_registry_name = local.operations_container_registry_name
  # ops_resource_group_name     = local.operations_resource_group_name
}

# module "vpc" {
#   source                         = "../../modules/vpc/"
#   deployment_namespace           = var.deployment_namespace
#   deployment_location            = var.deployment_location
#   virtual_network                = var.virtual_network
#   # networks                       = var.networks
#   # route_tables                   = var.route_tables
#   owner                          = var.owner
#   name                           = var.name
#   dns_servers                    = []
#   # service_endpoints              = var.service_endpoints
#   # routes                         = var.routes
#   # virtual_appliance_routes       = "${var.virtual_appliance_routes["aks"]},${module.private-aks-firewall.ip_config[0].private_ip_address}"
#   # virtual_appliance_route_tables = var.virtual_appliance_route_tables
# }

# module "private-aks-firewall" {
#   source              = "../../modules/azure_firewall"
#   resource_group_name = azurerm_resource_group.vpc.name
#   location            = var.deployment_location
#   name                = var.name
#   environment         = var.deployment_namespace
#   subnet_id           = azurerm_subnet.AzureFirewallSubnet.id
#   az_fw_ip            = azurerm_public_ip.az_fw_ip.id
# }

# module "k8s" {
#   source                   = "../../modules/k8s"
#   region                   = var.deployment_location
#   name                     = var.name
#   environment              = var.deployment_namespace
#   owner                    = var.owner
#   k8s_dns_prefix           = var.k8s_dns_prefix
#   k8s_node_size            = "Standard_D2_v3"
#   vnet_subnet_id           = azurerm_subnet.aks.id
#   enable_auto_scaling      = true
#   max_count                = var.aks_max_node_count
#   min_count                = var.aks_min_node_count
#   client_id                = module.aks_sp.application_id
#   client_secret            = module.aks_sp.application_password
#   client_object_id         = module.aks_sp.object_id
#   workspace_id             = local.log_analytics_workspace_id
#   vnet_id                  = azurerm_virtual_network.vpc.id
#   node_resource_group      = "${var.name}-node-rg-${var.deployment_namespace}"
#   virtual_network          = var.virtual_network
#   vnet_resource_group_name = azurerm_resource_group.vpc.name
#   aks_subnet_id            = azurerm_subnet.aks.id
#   aks_route_table          = "${var.name}-aks-${var.deployment_namespace}"
#   depends_on               = [module.aks_sp, module.keyvault_reader_identity]
# }

# module "keyvault" {
#   source             = "../../modules/keyvault"
#   name               = "cz"
#   region             = var.deployment_location
#   owner              = var.owner
#   environment        = var.deployment_namespace
#   tenant_id          = data.azurerm_client_config.azure_client.tenant_id
#   principal_id_count = 1
#   principal_id       = module.keyvault_reader_identity.principal_id
#   admin_principals   = { "operator" : data.azurerm_client_config.azure_client.object_id }
#   tenant_principals  = {}
#   policy             = "Deny"
#   subnet_ids         = [azurerm_subnet.aks.id, local.deployment_subnet_id]
#   whitelist          = { "operator" = local.operator_ip }
#   workspace_id       = local.log_analytics_workspace_id
# }

# module "tenant_keyvault" {
#   source            = "../../modules/keyvault"
#   name              = "tenants"
#   region            = var.deployment_location
#   owner             = var.owner
#   environment       = var.deployment_namespace
#   tenant_id         = data.azurerm_client_config.azure_client.tenant_id
#   principal_id      = data.azurerm_client_config.azure_client.object_id
#   tenant_principals = { "${module.tenant_keyvault_app.name}" = "${module.tenant_keyvault_app.sp_object_id}" }
#   admin_principals  = {}
#   policy            = "Deny"
#   subnet_ids        = [azurerm_subnet.aks.id]
#   whitelist         = { "operator" = local.operator_ip }
#   workspace_id      = local.log_analytics_workspace_id
# }

# DO NOT DELETE YET - Not clear to me this is needed/used for anything.
# Need to ask Mike P.
# module "operator_keyvault" {
#   source            = "../../modules/keyvault"
#   name              = "ops"
#   region            = var.deployment_location
#   owner             = var.owner
#   environment       = var.deployment_namespace
#   tenant_id         = data.azurerm_client_config.azure_client.tenant_id
#   principal_id      = data.azurerm_client_config.azure_client.object_id
#   admin_principals  = { "operator" : data.azurerm_client_config.azure_client.object_id }
#   tenant_principals = { (module.ops_keyvault_app.name) = "${module.ops_keyvault_app.sp_object_id}" }
#   policy            = "Deny"
#   subnet_ids        = [azurerm_subnet.aks.id, local.deployment_subnet_id]
#   whitelist         = { "operator" = local.operator_ip }
#   workspace_id      = local.log_analytics_workspace_id
# }

# module "bastion" {
#   source                     = "../../modules/bastion"
#   rg                         = "${var.deployment_namespace}-bastion-jump"
#   region                     = var.deployment_location
#   mgmt_subnet_rg             = azurerm_resource_group.vpc.name
#   mgmt_subnet_vpc_name       = azurerm_virtual_network.vpc.name
#   bastion_subnet_rg          = azurerm_resource_group.vpc.name
#   bastion_subnet_vpc_name    = azurerm_virtual_network.vpc.name
#   mgmt_subnet_cidr           = "10.1.250.0/24"
#   bastion_subnet_cidr        = "10.1.4.0/24"
#   bastion_aks_sp_secret      = module.bastion_sp.application_password
#   bastion_aks_sp_id          = module.bastion_sp.application_id
#   environment                = var.deployment_namespace
#   owner                      = var.owner
#   name                       = var.name
#   bastion_ssh_pub_key_path   = "" # TODO(jesse) Unused.
#   log_analytics_workspace_id = local.log_analytics_workspace_id
#   registry_password          = var.OPS_SEC
#   registry_username          = var.OPS_CID
#   depends_on                 = [module.vpc]
#   container_registry         = local.operations_container_registry
# }

# module "ops_keyvault_app" {
#   source = "../../modules/azure_ad"
#   name   = "ops-keyvault-sp"
#   deployment_namespace = var.deployment_namespace
# }
