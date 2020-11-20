variable "environment" {}
variable "location" {}
variable "resource_group_name" {}
variable "subnet_id" {}
variable "name" {}
variable "az_fw_ip" {}
variable "az_fw_ip_id" {}
variable "nat_rules_translated_ips" {}
variable "virtual_appliance_routes" {}
variable "virtual_appliance_route_tables" {}
variable "vnet_cidr" {}
variable "subnets" {
type = map
}
variable "maintenance_page_ip" {}
