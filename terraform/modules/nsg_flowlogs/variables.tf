variable "name" {}
variable "location" {}
variable "environment" {}
variable "vpc_name" {}
variable "resource_group_name" {}
variable "security_group_ids" {
  type = "list"
}
variable "log_workspace_id" {}
variable "workspace_resource_id" {}
