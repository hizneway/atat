output "id" {
  value = azurerm_firewall.fw.id
}


output "ip_config" {

  value = azurerm_firewall.fw.ip_configuration
}

output "nat_rule_ips" {

  value = var.nat_rules_translated_ips
}
