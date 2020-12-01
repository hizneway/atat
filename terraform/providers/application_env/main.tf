data "http" "myip" {
  url = "http://ipinfo.io/ip"
}

data "azurerm_client_config" "azure_client" {
}

locals {
  private_aks_appliance_routes               = var.virtual_appliance_routes["aks-private"]
  deployment_subnet_id                       = data.terraform_remote_state.previous_stage.outputs.operations_deployment_subnet_id
  operations_container_registry = data.terraform_remote_state.previous_stage.outputs.operations_container_registry_login_server
  operations_resource_group_name             = data.terraform_remote_state.previous_stage.outputs.operations_resource_group_name
  operations_storage_account_name = data.terraform_remote_state.previous_stage.outputs.operations_storage_account_name
  operator_ip                                = chomp(data.http.myip.body)
  log_analytics_workspace_id                 = data.terraform_remote_state.previous_stage.outputs.logging_workspace_id
}

module "tenant_keyvault_app" {
  source = "../../modules/azure_ad"
  name   = "tenant-keyvault"
}

module "aks_sp" {
  source = "../../modules/azure_ad"
  name   = "aks-service-principal"
}

module "bastion_sp" {
  source = "../../modules/azure_ad"
  name   = "bastion-service-principal"
}

module "ops_keyvault_app" {
  source = "../../modules/azure_ad"
  name   = "ops-keyvault-sp"
}

# module "bastion" {
#   source                     = "../../modules/bastion"
#   rg                         = "${var.deployment_namespace}-bastion-jump"
#   region                     = var.deployment_location
#   mgmt_subnet_rg             = module.vpc.resource_group_name
#   mgmt_subnet_vpc_name       = module.vpc.vpc_name
#   bastion_subnet_rg          = module.vpc.resource_group_name
#   bastion_subnet_vpc_name    = module.vpc.vpc_name
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
  subnet_ids             = [module.vpc.subnet_list["aks"].id]
  whitelist              = { "operator" = local.operator_ip }
  bucket_cors_properties = var.bucket_cors_properties
  storage_container_name = var.task_order_bucket_storage_container_name
  depends_on             = [module.vpc]
}

module "container_registry" {
  source                      = "../../modules/container_registry"
  name                        = var.name
  region                      = var.deployment_location
  environment                 = var.deployment_namespace
  owner                       = var.owner
  backup_region               = "" # TODO(jesse) Unused.
  policy                      = "Allow"
  subnet_ids                  = [module.vpc.subnet_list["aks"].id]
  whitelist                   = { "operator" = local.operator_ip }
  workspace_id                = local.log_analytics_workspace_id
  pet_name                    = var.deployment_namespace
  subnet_list                 = module.vpc.subnet_list
  depends_on                  = [module.vpc]
  # ops_container_registry_name = local.operations_container_registry_name
  # ops_resource_group_name     = local.operations_resource_group_name
}

module "keyvault_reader_identity" {
  source      = "../../modules/managed_identity"
  name        = var.name
  owner       = var.owner
  environment = var.deployment_namespace
  region      = var.deployment_location
  identity    = "${var.name}-${var.deployment_namespace}-vault-reader"
  roles       = ["Reader", "Managed Identity Operator"]
}

# module "k8s" {
#   source                   = "../../modules/k8s"
#   region                   = var.deployment_location
#   name                     = var.name
#   environment              = var.deployment_namespace
#   owner                    = var.owner
#   k8s_dns_prefix           = var.k8s_dns_prefix
#   k8s_node_size            = "Standard_D2_v3"
#   vnet_subnet_id           = module.vpc.subnet_list["aks"].id
#   enable_auto_scaling      = true
#   max_count                = var.aks_max_node_count
#   min_count                = var.aks_min_node_count
#   client_id                = module.aks_sp.application_id
#   client_secret            = module.aks_sp.application_password
#   client_object_id         = module.aks_sp.object_id
#   workspace_id             = local.log_analytics_workspace_id
#   vnet_id                  = module.vpc.id
#   node_resource_group      = "${var.name}-node-rg-${var.deployment_namespace}"
#   virtual_network          = var.virtual_network
#   vnet_resource_group_name = module.vpc.resource_group_name
#   aks_subnet_id            = module.vpc.subnet_list["aks"].id
#   aks_route_table          = "${var.name}-aks-${var.deployment_namespace}"
#   depends_on               = [module.aks_sp, module.keyvault_reader_identity]
# }

module "keyvault" {
  source             = "../../modules/keyvault"
  name               = "cz"
  region             = var.deployment_location
  owner              = var.owner
  environment        = var.deployment_namespace
  tenant_id          = data.azurerm_client_config.azure_client.tenant_id
  principal_id_count = 1
  principal_id       = module.keyvault_reader_identity.principal_id
  admin_principals   = { "operator" : data.azurerm_client_config.azure_client.object_id }
  tenant_principals  = {}
  policy             = "Deny"
  subnet_ids         = [module.vpc.subnet_list["aks"].id, local.deployment_subnet_id]
  whitelist          = { "operator" = local.operator_ip }
  workspace_id       = local.log_analytics_workspace_id
}

resource "azurerm_key_vault_secret" "secret" {
  for_each = merge(var.keyvault_secrets, {
    "AZURE-CLIENT-ID"   = module.tenant_keyvault_app.application_id
    "AZURE-SECRET-KEY"  = module.tenant_keyvault_app.application_password
    "AZURE-TENANT-ID"   = data.azurerm_client_config.azure_client.tenant_id
    "AZURE-STORAGE-KEY" = module.task_order_bucket.primary_access_key
    "REDIS-PASSWORD"    = azurerm_redis_cache.redis.primary_access_key
    "SAML-IDP-CERT"     = ""
    "PGPASSWORD"        = random_password.atat_user_password.result
    "AZURE-VAULT-URL"   = module.tenant_keyvault.url
    "DHPARAMS"          = filebase64(var.dhparams_path)
  })

  name         = each.key
  value        = each.value
  key_vault_id = module.keyvault.id
  depends_on = [module.keyvault.keyvault_spun_up]
}

resource "azurerm_key_vault_certificate" "atatdev" {
  name         = "atatdev"
  key_vault_id = module.keyvault.id
  certificate {
    contents = filebase64(var.tls_cert_path)
    password = ""
  }
  certificate_policy {
    issuer_parameters {
      name = "Unknown"
    }

    key_properties {
      exportable = true
      key_size   = 2048
      key_type   = "RSA"
      reuse_key  = false
    }
    secret_properties {
      content_type = "application/x-pem-file"
    }
  }
  depends_on = [module.keyvault.keyvault_spun_up]
}

module "tenant_keyvault" {
  source            = "../../modules/keyvault"
  name              = "tenants"
  region            = var.deployment_location
  owner             = var.owner
  environment       = var.deployment_namespace
  tenant_id         = data.azurerm_client_config.azure_client.tenant_id
  principal_id      = data.azurerm_client_config.azure_client.object_id
  tenant_principals = { "${module.tenant_keyvault_app.name}" = "${module.tenant_keyvault_app.sp_object_id}" }
  admin_principals  = {}
  policy            = "Deny"
  subnet_ids        = [module.vpc.subnet_list["aks"].id]
  whitelist         = { "operator" = local.operator_ip }
  workspace_id      = local.log_analytics_workspace_id
}

module "operator_keyvault" {
  source            = "../../modules/keyvault"
  name              = "ops"
  region            = var.deployment_location
  owner             = var.owner
  environment       = var.deployment_namespace
  tenant_id         = data.azurerm_client_config.azure_client.tenant_id
  principal_id      = data.azurerm_client_config.azure_client.object_id
  admin_principals  = { "operator" : data.azurerm_client_config.azure_client.object_id }
  tenant_principals = { (module.ops_keyvault_app.name) = "${module.ops_keyvault_app.sp_object_id}" }
  policy            = "Deny"
  subnet_ids        = [module.vpc.subnet_list["aks"].id, local.deployment_subnet_id]
  whitelist         = { "operator" = local.operator_ip }
  workspace_id      = local.log_analytics_workspace_id
}

# module "logs" {
#   source            = "../../modules/log_analytics"
#   owner             = var.owner
#   environment       = var.deployment_namespace
#   region            = var.deployment_location
#   name              = var.name
#   retention_in_days = 365
# }

resource "random_password" "pg_root_password" {
  length           = 16
  min_numeric      = 1
  special          = true
  override_special = "!"
}

resource "random_password" "atat_user_password" {
  length           = 15
  min_numeric      = 0
  special          = false
  override_special = "!"
}

# module "sql" {
#   source                       = "../../modules/postgres"
#   name                         = var.name
#   owner                        = var.owner
#   environment                  = var.deployment_namespace
#   region                       = var.deployment_location
#   subnet_id                    = module.vpc.subnet_list["aks"].id
#   administrator_login          = var.postgres_admin_login
#   administrator_login_password = random_password.pg_root_password.result
#   workspace_id                 = local.log_analytics_workspace_id
#   operator_ip                  = chomp(data.http.myip.body)
#   deployment_subnet_id         = local.deployment_subnet_id
# }

resource "azurerm_resource_group" "sql" {
  name     = "${var.deployment_namespace}-postgres"
  location = var.deployment_location
}

resource "azurerm_postgresql_server" "sql" {
  name                = "${var.deployment_namespace}-sql"
  location            = azurerm_resource_group.sql.location
  resource_group_name = azurerm_resource_group.sql.name
  sku_name = "GP_Gen5_2"

  storage_mb                   = "5120"
  backup_retention_days        = "7"
  geo_redundant_backup_enabled = false
  auto_grow_enabled            = true

  administrator_login          = "clouzero_pg_admin"
  administrator_login_password = random_password.pg_root_password.result
  version                      = "10"
  ssl_enforcement_enabled      = true

}

resource "azurerm_postgresql_virtual_network_rule" "allow_aks_subnet" {
  name                                 = "allow-aks-subnet-rule"
  resource_group_name                  = azurerm_resource_group.sql.name
  server_name                          = azurerm_postgresql_server.sql.name
  subnet_id                            = module.vpc.subnet_list["aks"].id
  ignore_missing_vnet_service_endpoint = true
}

resource "azurerm_postgresql_virtual_network_rule" "allow_deployment_subnet" {
  name                                 = "allow-deployment-subnet-rule"
  resource_group_name                  = azurerm_resource_group.sql.name
  server_name                          = azurerm_postgresql_server.sql.name
  subnet_id                            = local.deployment_subnet_id
  ignore_missing_vnet_service_endpoint = true
}

resource "azurerm_postgresql_virtual_network_rule" "allow_management_subnet" {
  name                                 = "allow-management-subnet-rule"
  resource_group_name                  = azurerm_resource_group.sql.name
  server_name                          = azurerm_postgresql_server.sql.name
  subnet_id                            = azurerm_subnet.mgmt_subnet.id
  ignore_missing_vnet_service_endpoint = true
}

resource "azurerm_postgresql_firewall_rule" "operator" {
  name                = "operator"
  resource_group_name = azurerm_resource_group.sql.name
  server_name         = azurerm_postgresql_server.sql.name
  start_ip_address    = chomp(data.http.myip.body)
  end_ip_address      = chomp(data.http.myip.body)
}

resource "azurerm_postgresql_database" "db" {
  name                = "${var.deployment_namespace}-atat"
  resource_group_name = azurerm_resource_group.sql.name
  server_name         = azurerm_postgresql_server.sql.name
  charset             = "UTF8"
  collation           = "en-US"
}



resource "azurerm_kubernetes_cluster" "k8s_private" {
  name                    = "${var.name}-private-k8s-${var.deployment_namespace}"
  location                = var.deployment_location
  resource_group_name     = module.vpc.resource_group_name
  dns_prefix              = "atat-aks-private"
  private_cluster_enabled = true
  node_resource_group     = "${module.vpc.resource_group_name}-private-aks-node-rgs"
  addon_profile {
    azure_policy {
      enabled = true
    }
    oms_agent {
      enabled                    = true
      log_analytics_workspace_id = local.log_analytics_workspace_id
    }
  }
  network_profile {

    network_plugin     = "azure"
    dns_service_ip     = var.private_aks_service_dns
    docker_bridge_cidr = var.private_aks_docker_bridge_cidr
    outbound_type      = "userDefinedRouting"
    service_cidr       = var.private_aks_service_cidr
    load_balancer_sku  = "Standard"
  }
  identity {
    type = "SystemAssigned"
  }
  # service_principal {
  #   client_id     = var.private_aks_sp_id
  #   client_secret = var.private_aks_sp_secret
  # }

  default_node_pool {
    name                  = "default"
    vm_size               = "Standard_B2s"
    os_disk_size_gb       = 30
    vnet_subnet_id        = module.vpc.subnet_list["aks-private"].id
    enable_node_public_ip = false
    enable_auto_scaling   = false
    node_count            = 1
  }

  lifecycle {
    ignore_changes = [
      default_node_pool.0.node_count
    ]
  }

  tags = {
    Name        = "private-aks-atat"
    environment = var.deployment_namespace
    owner       = var.owner
  }
  depends_on = [module.vpc, module.keyvault_reader_identity]
}

# module "private-k8s" {
#   source                     = "../../modules/k8s-private"
#   rg                         = module.vpc.resource_group_name
#   region                     = var.deployment_location
#   name                       = var.name
#   environment                = var.deployment_namespace
#   owner                      = var.owner
#   k8s_dns_prefix             = var.k8s_dns_prefix
#   k8s_node_size              = "Standard_D2_v3"
#   enable_auto_scaling        = true
#   max_count                  = 3
#   min_count                  = 3
#   private_aks_sp_id          = var.private_aks_sp_id
#   private_aks_sp_secret      = var.private_aks_sp_secret
#   log_analytics_workspace_id = local.log_analytics_workspace_id
#   service_dns                = var.private_aks_service_dns
#   docker_bridge_cidr         = var.private_aks_docker_bridge_cidr
#   service_cidr               = var.private_aks_service_cidr
#   subnet_cidr                = var.private_k8s_subnet_cidr
#   vnet_id                    = module.vpc.id
#   vpc_name                   = module.vpc.vpc_name
#   aks_subnet_id              = module.vpc.subnet_list["aks-private"].id
#   vpc_address_space          = "10.1.0.0/16"

#   depends_on = [module.vpc, module.keyvault_reader_identity]
# }

module "private-aks-firewall" {

  source              = "../../modules/azure_firewall"
  resource_group_name = module.vpc.resource_group_name
  location            = var.deployment_location
  name                = var.name
  environment         = var.deployment_namespace
  subnet_id           = module.vpc.subnet_list["AzureFirewallSubnet"].id
  az_fw_ip            = module.vpc.fw_ip_address_id
}

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
  subnet_id           = module.vpc.subnet_list["redis"].id

  redis_configuration {
    enable_authentication = true
  }
  tags = {
    environment = var.deployment_namespace
    owner       = var.owner
  }
}


module "vpc" {
  source                         = "../../modules/vpc/"
  environment                    = var.deployment_namespace
  region                         = var.deployment_location
  virtual_network                = var.virtual_network
  networks                       = var.networks
  route_tables                   = var.route_tables
  owner                          = var.owner
  name                           = var.name
  dns_servers                    = []
  service_endpoints              = var.service_endpoints
  custom_routes                  = var.routes
  virtual_appliance_routes       = "${var.virtual_appliance_routes["aks-private"]},${module.private-aks-firewall.ip_config[0].private_ip_address}"
  virtual_appliance_route_tables = var.virtual_appliance_route_tables
}


resource "azurerm_resource_group" "jump" {
  name     = "${var.name}-bastion-${var.deployment_namespace}"
  location = var.deployment_location
}


# add mgmgt subnet

resource "azurerm_subnet" "mgmt_subnet" {
  name                 = "mgmt-subnet"
  resource_group_name  = module.vpc.resource_group_name
  virtual_network_name = module.vpc.vpc_name
  address_prefixes     = ["10.1.250.0/24"]

  enforce_private_link_endpoint_network_policies = true

  service_endpoints = ["Microsoft.KeyVault", "Microsoft.ContainerRegistry", "Microsoft.Sql"]

  delegation {
    name = "delegation"

    service_delegation {
      name    = "Microsoft.ContainerInstance/containerGroups"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

resource "azurerm_network_profile" "bastion" {
  name                = "examplenetprofile"
  location            = azurerm_resource_group.jump.location
  resource_group_name = azurerm_resource_group.jump.name

  container_network_interface {
    name = "bastionnic"

    ip_configuration {
      name      = "bastionipconfig"
      subnet_id = azurerm_subnet.mgmt_subnet.id
    }
  }
}

# Bastion
resource "azurerm_container_group" "bastion" {
  name                = "bastion"
  location            = azurerm_resource_group.jump.location
  resource_group_name = azurerm_resource_group.jump.name
  ip_address_type     = "private"
  network_profile_id  = azurerm_network_profile.bastion.id
  os_type             = "Linux"

  container {
    name     = "bastion"
    image    = "${local.operations_container_registry}/ops:latest"
    cpu      = "1"
    memory   = "2"
    commands = ["tail", "-f", "/dev/null"]

    ports {
      port     = 443
      protocol = "TCP"
    }

    secure_environment_variables = {
      "SP_CLIENT_ID" = var.operator_client_id
      "SP_CLIENT_SECRET" = var.operator_client_secret
      "TENANT_ID" = var.operator_tenant_id
      "SUBSCRIPTION_ID" = var.operator_subscription_id
      "OPS_REGISTRY" = local.operations_container_registry
      "NAMESPACE" = var.deployment_namespace
      "OPS_RESOURCE_GROUP" = local.operations_resource_group_name
      "OPS_STORAGE_ACCOUNT" = local.operations_storage_account_name
    }
  }

  image_registry_credential {
    username = var.operator_client_id
    password = var.operator_client_secret
    server   = local.operations_container_registry
  }

  tags = {
    environment = "testing"
  }
}
