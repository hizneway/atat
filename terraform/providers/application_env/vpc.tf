resource "azurerm_resource_group" "vpc" {
  name     = "${var.name}-vpc-${var.deployment_namespace}"
  location = var.deployment_location

  tags = {
    environment = var.deployment_namespace
    owner       = var.owner
  }
}

resource "azurerm_network_ddos_protection_plan" "vpc" {
  count               = var.ddos_enabled
  name                = "${var.name}-ddos-${var.deployment_namespace}"
  location            = azurerm_resource_group.vpc.location
  resource_group_name = azurerm_resource_group.vpc.name
}

resource "azurerm_virtual_network" "vpc" {
  name                = "${var.name}-network-${var.deployment_namespace}"
  location            = azurerm_resource_group.vpc.location
  resource_group_name = azurerm_resource_group.vpc.name
  address_space       = ["${var.virtual_network}"] # TODO(jesse) Can this be wired up dynamically?
  dns_servers         = []

  tags = {
    environment = var.deployment_namespace
    owner       = var.owner
  }
}

# resource "azurerm_subnet" "subnet" {
#   for_each             = var.networks
#   name                 = "${each.key == "AzureFirewallSubnet" ? "AzureFirewallSubnet" : "${var.name}-${each.key}-${var.deployment_namespace}"}"
#   resource_group_name  = azurerm_resource_group.vpc.name
#   virtual_network_name = azurerm_virtual_network.vpc.name
#   address_prefixes     = [element(split(",", each.value), 0)]
#   service_endpoints    = split(",", var.service_endpoints[each.key])
# }

# aks subnet
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
resource "azurerm_route" "aks_to_internet" {
  name                = "${var.name}-default-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name    = azurerm_route_table.aks.name
  address_prefix      = "0.0.0.0/0"
  next_hop_type       = "Internet"
}
resource "azurerm_route" "aks_to_vnet" {
  name = "${var.name}-vnet-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name = azurerm_route_table.aks.name
  address_prefix = "10.1.0.0/16"
  next_hop_type = "VnetLocal"
}

# edge subnet
resource "azurerm_subnet" "edge" {
  name = "${var.name}-edge-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  virtual_network_name = azurerm_virtual_network.vpc.name
  address_prefixes = ["10.1.1.0/24"]
  service_endpoints = ["Microsoft.ContainerRegistry"]
}

resource "azurerm_route_table" "edge" {
  name = "${var.name}-edge-${var.deployment_namespace}"
  location = azurerm_resource_group.vpc.location
  resource_group_name = azurerm_resource_group.vpc.name
}
resource "azurerm_subnet_route_table_association" "edge" {
  subnet_id = azurerm_subnet.edge.id
  route_table_id = azurerm_route_table.edge.id
}
resource "azurerm_route" "edge_to_internet" {
  name                = "${var.name}-default-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name    = azurerm_route_table.edge.name
  address_prefix      = "0.0.0.0/0"
  next_hop_type       = "Internet"
}
resource "azurerm_route" "edge_to_vnet" {
  name = "${var.name}-vnet-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name = azurerm_route_table.edge.name
  address_prefix = "10.1.0.0/16"
  next_hop_type = "VnetLocal"
}


# redis subnet
resource "azurerm_subnet" "redis" {
  name = "${var.name}-redis-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  virtual_network_name = azurerm_virtual_network.vpc.name
  address_prefixes = ["10.1.3.0/24"]
  service_endpoints = [
    "Microsoft.Storage",
    "Microsoft.Sql"
  ]
}

resource "azurerm_route_table" "redis" {
  name = "${var.name}-redis-${var.deployment_namespace}"
  location = azurerm_resource_group.vpc.location
  resource_group_name = azurerm_resource_group.vpc.name
}
resource "azurerm_subnet_route_table_association" "redis" {
  subnet_id = azurerm_subnet.redis.id
  route_table_id = azurerm_route_table.redis.id
}
resource "azurerm_route" "redis_to_internet" {
  name                = "${var.name}-default-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name    = azurerm_route_table.redis.name
  address_prefix      = "0.0.0.0/0"
  next_hop_type       = "Internet"
}
resource "azurerm_route" "redis_to_vnet" {
  name = "${var.name}-vnet-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name = azurerm_route_table.redis.name
  address_prefix = "10.1.0.0/16"
  next_hop_type = "VnetLocal"
}

# AzureFirewallSubnet
resource "azurerm_subnet" "AzureFirewallSubnet" {
  name = "AzureFirewallSubnet"
  resource_group_name = azurerm_resource_group.vpc.name
  virtual_network_name = azurerm_virtual_network.vpc.name
  address_prefixes = ["10.1.4.0/24"]
  service_endpoints = []
}

resource "azurerm_route_table" "AzureFirewallSubnet" {
  name = "${var.name}-AzureFirewallSubnet-${var.deployment_namespace}"
  location = azurerm_resource_group.vpc.location
  resource_group_name = azurerm_resource_group.vpc.name
}
resource "azurerm_subnet_route_table_association" "AzureFirewallSubnet" {
  subnet_id = azurerm_subnet.AzureFirewallSubnet.id
  route_table_id = azurerm_route_table.AzureFirewallSubnet.id
}
resource "azurerm_route" "AzureFirewallSubnet_to_internet" {
  name                = "${var.name}-default-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name    = azurerm_route_table.AzureFirewallSubnet.name
  address_prefix      = "0.0.0.0/0"
  next_hop_type       = "Internet"
}
resource "azurerm_route" "AzureFirewallSubnet_to_vnet" {
  name = "${var.name}-vnet-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name = azurerm_route_table.AzureFirewallSubnet.name
  address_prefix = "10.1.0.0/16"
  next_hop_type = "VnetLocal"
}

# appgateway
resource "azurerm_subnet" "appgateway" {
  name = "${var.name}-appgateway-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  virtual_network_name = azurerm_virtual_network.vpc.name
  address_prefixes = ["10.1.6.0/24"]
  service_endpoints = []
}

resource "azurerm_route_table" "appgateway" {
  name = "${var.name}-appgateway-${var.deployment_namespace}"
  location = azurerm_resource_group.vpc.location
  resource_group_name = azurerm_resource_group.vpc.name
}
resource "azurerm_subnet_route_table_association" "appgateway" {
  subnet_id = azurerm_subnet.appgateway.id
  route_table_id = azurerm_route_table.appgateway.id
}
resource "azurerm_route" "appgateway_to_internet" {
  name                = "${var.name}-default-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name    = azurerm_route_table.appgateway.name
  address_prefix      = "0.0.0.0/0"
  next_hop_type       = "Internet"
}
resource "azurerm_route" "appgateway_to_vnet" {
  name = "${var.name}-vnet-${var.deployment_namespace}"
  resource_group_name = azurerm_resource_group.vpc.name
  route_table_name = azurerm_route_table.appgateway.name
  address_prefix = "10.1.0.0/16"
  next_hop_type = "VnetLocal"
}


# resource "azurerm_route_table" "route_table" {
#   for_each            = var.route_tables
#   name                = "${var.name}-${each.key}-${var.deployment_namespace}"
#   location            = azurerm_resource_group.vpc.location
#   resource_group_name = azurerm_resource_group.vpc.name
# }
# resource "azurerm_subnet_route_table_association" "route_table" {
#   for_each       = var.route_tables
#   subnet_id      = azurerm_subnet.subnet[each.key].id
#   route_table_id = azurerm_route_table.route_table[each.key].id
# }

# Default Routes
# resource "azurerm_route" "route" {
#   for_each            = var.route_tables
#   name                = "${var.name}-default-${var.deployment_namespace}"
#   resource_group_name = azurerm_resource_group.vpc.name
#   route_table_name    = azurerm_route_table.route_table[each.key].name
#   address_prefix      = "0.0.0.0/0"
#   next_hop_type       = each.value
# }

# Custom Routes
# resource "azurerm_route" "custom_routes" {
#   for_each            = var.routes
#   name                = "${var.name}-${element(split(",", each.value), 1)}-${var.deployment_namespace}"
#   resource_group_name = azurerm_resource_group.vpc.name
#   route_table_name    = azurerm_route_table.route_table[each.key].name
#   address_prefix      = element(split(",", each.value), 2)
#   next_hop_type       = element(split(",", each.value), 3)
# }

resource "azurerm_route_table" "aks_firewall_route_table" {
  name                = "${var.name}-aks-fw-${var.deployment_namespace}"
  location            = azurerm_resource_group.vpc.location
  resource_group_name = azurerm_resource_group.vpc.name
}

resource "azurerm_route" "aks_firewall_routes" {

  name                   = "${var.name}-aksfw-${var.deployment_namespace}"
  resource_group_name    = azurerm_resource_group.vpc.name
  route_table_name       = azurerm_route_table.aks_firewall_route_table.name
  address_prefix         = "10.1.0.0/16"
  next_hop_type          = "VirtualAppliance"
  next_hop_in_ip_address = azurerm_firewall.fw.ip_configuration[0].private_ip_address
}

resource "azurerm_subnet_route_table_association" "aks_firewall_route_table" {
  # for_each       = var.virtual_appliance_route_tables
  subnet_id      = azurerm_subnet.aks.id
  route_table_id = azurerm_route_table.aks_firewall_route_table.id
}

# Default Routes
resource "azurerm_route" "fw_route" {
  name                   = "${var.name}-default-${var.deployment_namespace}"
  resource_group_name    = azurerm_resource_group.vpc.name
  route_table_name       = azurerm_route_table.aks_firewall_route_table.name
  address_prefix         = "0.0.0.0/0"
  next_hop_type          = "VirtualAppliance"
  next_hop_in_ip_address = azurerm_firewall.fw.ip_configuration[0].private_ip_address
}

resource "azurerm_public_ip" "az_fw_ip" {
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
    subnet_id            = azurerm_subnet.AzureFirewallSubnet.id
    public_ip_address_id = azurerm_public_ip.az_fw_ip.id
  }
}

resource "azurerm_firewall_application_rule_collection" "fw_rule_collection" {
  name                = "aksbasics"
  azure_firewall_name = "az-firewall-${var.deployment_namespace}"
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

  depends_on = [azurerm_firewall.fw]

}
