terraform {
  required_providers {
    azuread = {
      source = "hashicorp/azuread"
      version = "= 1.0.0"
    }

    azurerm = {
      source = "hashicorp/azurerm"
      version = "= 2.34.0"
    }
  }
}

resource "random_pet" "unique_id" {
  length    = 1
  separator = ""
}

locals {
  environment = length(var.environment) > 0 ? var.environment : random_pet.unique_id.id
}
