resource "azurerm_route_table" "firewall_route_table" {
  for_each            = var.virtual_appliance_route_tables
  name                = "${var.name}-${each.key}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_route" "firewall_routes" {
  for_each            = var.virtual_appliance_routes
  name                = "${var.name}-${each.key}-${var.environment}"
  resource_group_name = var.resource_group_name
  route_table_name    = "${var.name}-${each.key}-${var.environment}"
  address_prefix      = var.vnet_cidr
  next_hop_type       = "VnetLocal"
}

resource "azurerm_route" "firewall_routes_public" {
  for_each            = var.virtual_appliance_routes
  name                = "${var.name}-${element(split(",", each.value), 0)}-${var.environment}-public"
  resource_group_name = var.resource_group_name
  route_table_name    = azurerm_route_table.firewall_route_table[each.key].name
  address_prefix      = "${var.az_fw_ip}/32"
  next_hop_type       = "Internet"
}

resource "azurerm_subnet_route_table_association" "firewall_route_table" {
  for_each       = var.virtual_appliance_route_tables
  subnet_id      = var.subnets[each.key].id
  route_table_id = azurerm_route_table.firewall_route_table[each.key].id
}

# Default Routes
resource "azurerm_route" "fw_route" {
  for_each               = var.virtual_appliance_route_tables
  name                   = "${var.name}-default-${var.environment}"
  resource_group_name    = var.resource_group_name
  route_table_name       = azurerm_route_table.firewall_route_table[each.key].name
  address_prefix         = "0.0.0.0/0"
  next_hop_type          = each.value
  next_hop_in_ip_address = azurerm_firewall.fw.ip_configuration[0].private_ip_address
}

resource "azurerm_firewall" "fw" {
  name                = "az-firewall-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name

  ip_configuration {
    name                 = "configuration"
    subnet_id            = var.subnet_id
    public_ip_address_id = var.az_fw_ip_id
  }
}

resource "azurerm_firewall_application_rule_collection" "fw_rule_collection" {
  name                = "aksbasics"
  azure_firewall_name = "az-firewall-${var.environment}"
  resource_group_name = var.resource_group_name
  priority            = 101
  action              = "Allow"
  depends_on          = [azurerm_firewall.fw]

  rule {
    name             = "allow azure"
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

  rule {
    name             = "allow k8s"
    source_addresses = ["*"]
    fqdn_tags        = ["AzureKubernetesService"]
  }
}

resource "azurerm_firewall_nat_rule_collection" "tolb" {
  name                = "tolb"
  azure_firewall_name = azurerm_firewall.fw.name
  resource_group_name = var.resource_group_name
  priority            = 100
  action              = "Dnat"

  rule {
    name = "tok8slb"
    source_addresses = [
      "*",
    ]
    destination_ports = [
      "443",
    ]
    destination_addresses = [
      var.az_fw_ip
    ]
    translated_port    = 443
    translated_address = "${var.nat_rules_translated_ips}"
    protocols = [
      "TCP"
    ]
  }

  rule {
    name = "maintenancepage"
    source_addresses = [
      "*",
    ]
    destination_ports = [
      "443",
    ]
    destination_addresses = [
      var.az_fw_ip
    ]
    translated_port    = 443
    translated_address = "${var.maintenance_page_ip}"
    protocols = [
      "TCP"
    ]
  }

  timeouts {
    create = "30h"
    update = "30h"
    read   = "30h"
    delete = "30h"
  }
}
