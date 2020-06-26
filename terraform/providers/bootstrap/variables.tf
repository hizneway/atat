

source       = "../../modules/bucket"
service_name = "${var.name}${var.environment}tfstate"
owner        = var.owner
name         = var.name
environment  = var.environment
region       = var.region
policy       = "Deny"
subnet_ids   = []
whitelist    = var.storage_admin_whitelist
account_kind = "Storage"

variable "environment" {}

variable "region" {}

variable "owner" {}

variable "name" {}


variable "storage_admin_whitelist" {
  type = map
}
