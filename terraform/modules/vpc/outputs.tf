output "subnet_list" {
  value = {
    for k, id in azurerm_subnet.subnet : k => id
  }
}


output "address_space" { value=azurerm_virtual_network.vpc.address_space[0]}

output "subnet_address_prefixes" {

value = {
  for k, address_prefix in azurerm_subnet.subnet : k => address_prefix
}

}

output "id" {
  value = azurerm_virtual_network.vpc.id
}

output "vpc_name" {
  value = "${var.name}-${var.environment}-network"
}

output "resource_group_name" {

  value = "${var.name}-${var.environment}-vpc"

}
