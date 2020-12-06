output "id" {
  value = azurerm_firewall.fw.id
}


output "ip_config" {

  value = azurerm_firewall.fw.ip_configuration
}

output "nat_rule_ips" {

  value = var.nat_rules_translated_ips
}

output "rt_association_id" {
  value = azurerm_subnet_route_table_association.firewall_route_table
}
