# resource "azurerm_route_table" "aks" {
#   name = "${var.name}-aks-${var.deployment_namespace}"
#   location = azurerm_resource_group.vpc.location
#   resource_group_name = azurerm_resource_group.vpc.name
# }

# resource "azurerm_subnet_route_table_association" "aks" {
#   subnet_id = azurerm_subnet.aks.id
#   route_table_id = azurerm_route_table.aks.id
# }

# resource "azurerm_route" "aks_to_internet" {
#   name                = "${var.name}-default-${var.deployment_namespace}"
#   resource_group_name = azurerm_resource_group.vpc.name
#   route_table_name    = azurerm_route_table.aks.name
#   address_prefix      = "0.0.0.0/0"
#   next_hop_type       = "Internet"
# }

# resource "azurerm_route" "aks_to_vnet" {
#   name = "${var.name}-vnet-${var.deployment_namespace}"
#   resource_group_name = azurerm_resource_group.vpc.name
#   route_table_name = azurerm_route_table.aks.name
#   address_prefix = "10.1.0.0/16"
#   next_hop_type = "VnetLocal"
# }

# azure_firewall_subnet
resource "azurerm_subnet" "azure_firewall" {
  name = "azure_firewall"
  resource_group_name = azurerm_resource_group.vpc.name
  virtual_network_name = azurerm_virtual_network.vpc.name
  address_prefixes = ["10.1.4.0/24"]
  service_endpoints = []
}

resource "azurerm_route_table" "azure_firewall" {
  name = "${var.name}-fw-${var.deployment_namespace}"
  location = azurerm_resource_group.vpc.location
  resource_group_name = azurerm_resource_group.vpc.name
}

resource "azurerm_subnet_route_table_association" "azure_firewall" {
  subnet_id = azurerm_subnet.azure_firewall.id
  route_table_id = azurerm_route_table.azure_firewall.id
}

resource "azurerm_route" "azure_firewall_to_internet" {
  name = "default"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name = azurerm_route_table.azure_firewall.name
  address_prefix = "0.0.0.0/0"
  next_hop_type = "Internet"
}

resource "azurerm_public_ip" "azure_firewall_ip" {
  name                = "az-firewall-${var.deployment_namespace}"
  location            = var.deployment_location
  resource_group_name = azurerm_resource_group.vpc.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_firewall" "fw" {
  name                = "az-firewall-${var.deployment_namespace}"
  location            = var.deployment_location
  resource_group_name = azurerm_resource_group.vpc.name
  ip_configuration {
    name                 = "configuration"
    subnet_id            = azurerm_subnet.azure_firewall.id
    public_ip_address_id = azurerm_public_ip.azure_firewall_ip.id
  }
  tags = ["AzureKubernetesService"]
}

resource "azurerm_firewall_application_rule_collection" "fw_rule_collection" {
  name                = "aksbasics"
  azure_firewall_name = azurerm_firewall.fw.name
  resource_group_name = azurerm_resource_group.vpc.name
  priority            = 101
  action              = "Allow"
  rule {
    name             = "allow network"
    source_addresses = ["*"]
    target_fqdns = [
      "*.cdn.mscr.io",
      "mcr.microsoft.com",
      "*.data.mcr.microsoft.com",
      "management.azure.com",
      "login.microsoftonline.com",
      "acs-mirror.azureedge.net",
      "dc.services.visualstudio.com",
      "*.opinsights.azure.com",
      "*.oms.opinsights.azure.com",
      "*.microsoftonline.com",
      "*.monitoring.azure.com",
    ]
    protocol {
      port = "80"
      type = "Http"
    }
    protocol {
      port = "443"
      type = "Https"
    }
  }
  # depends_on = [azurerm_firewall.fw]
}

# aks
module "aks_sp" {
  source = "../../modules/azure_ad"
  name   = "aks-service-principal"
}

resource "azurerm_subnet" "aks" {
  name = "${var.name}-aks-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  virtual_network_name = azurerm_virtual_network.vpc.name
  address_prefixes = ["10.1.2.0/24"]
  service_endpoints = [
    "Microsoft.Storage",
    "Microsoft.KeyVault",
    "Microsoft.ContainerRegistry",
    "Microsoft.Sql"
  ]
}

resource "azurerm_route_table" "aks" {
  name = "${var.name}-aks-${var.deployment_namespace}"
  location = azurerm_resource_group.vpc.location
  resource_group_name = azurerm_resource_group.vpc.name
}
resource "azurerm_subnet_route_table_association" "aks" {
  subnet_id = azurerm_subnet.aks.id
  route_table_id = azurerm_route_table.aks.id
}
# resource "azurerm_route" "azure_firewall_to_internet" {
#   name                = "${var.name}-default-${var.deployment_namespace}"
#   resource_group_name = azurerm_resource_group.vpc.name
#   route_table_name    = azurerm_route_table.aks.name
#   address_prefix      = "0.0.0.0/0"
#   next_hop_type       = "Internet"
# }
resource "azurerm_route" "aks_to_vnet" {
  name = "to-vnet"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name = azurerm_route_table.aks.name
  address_prefix = "10.1.0.0/16"
  next_hop_type = "VnetLocal"
}
resource "azurerm_route" "aks_to_fw" {
  name = "to-fw"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name = azurerm_route_table.aks.name
  address_prefix = "0.0.0.0/0"
  next_hop_type = "VirtualAppliance"
  next_hop_in_ip_address = azurerm_firewall.fw.ip_configuration[0].private_ip_address
}

# resource "azurerm_route_table" "aks_firewall_route_table" {
#   name                = "${var.name}-aks-fw-${var.deployment_namespace}"
#   location            = azurerm_resource_group.vpc.location
#   resource_group_name = azurerm_resource_group.vpc.name
# }

# resource "azurerm_route" "aks_firewall_routes" {

#   name                   = "${var.name}-aksfw-${var.deployment_namespace}"
#   resource_group_name    = azurerm_resource_group.vpc.name
#   route_table_name       = azurerm_route_table.aks_firewall_route_table.name
#   address_prefix         = "10.1.0.0/16"
#   next_hop_type          = "VirtualAppliance"
#   next_hop_in_ip_address = azurerm_firewall.fw.ip_configuration[0].private_ip_address
# }

# resource "azurerm_subnet_route_table_association" "aks_firewall_route_table" {
#   # for_each       = var.virtual_appliance_route_tables
#   subnet_id      = azurerm_subnet.aks.id
#   route_table_id = azurerm_route_table.aks_firewall_route_table.id
# }

# # Default Routes
# resource "azurerm_route" "fw_route" {
#   name                   = "${var.name}-default-${var.deployment_namespace}"
#   resource_group_name    = azurerm_resource_group.vpc.name
#   route_table_name       = azurerm_route_table.aks_firewall_route_table.name
#   address_prefix         = "0.0.0.0/0"
#   next_hop_type          = "VirtualAppliance"
#   next_hop_in_ip_address = azurerm_firewall.fw.ip_configuration[0].private_ip_address
# }


resource "azurerm_kubernetes_cluster" "k8s_private" {
  name                    = "${var.name}-private-k8s-${var.deployment_namespace}"
  location                = var.deployment_location
  resource_group_name     = azurerm_resource_group.vpc.name
  dns_prefix              = "atat-aks"
  private_cluster_enabled = true
  node_resource_group     = "${azurerm_resource_group.vpc.name}-private-aks-node-rgs"
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
    vnet_subnet_id        = azurerm_subnet.aks.id
    enable_node_public_ip = false
    enable_auto_scaling   = false
    node_count            = 3
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
  depends_on = [module.keyvault_reader_identity]
  # depends_on = [module.vpc, module.keyvault_reader_identity]
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
