terraform {
  required_providers {
    azuread = {
      source  = "hashicorp/azuread"
      version = "= 1.0.0"
    }

    azurerm = {
      source  = "hashicorp/azurerm"
      version = "= 2.34.0"
    }
  }
}

locals {
  environment = "jesse"
  location    = "East US"
}

resource "azurerm_resource_group" "bootstrap_resource_group" {
  name     = "bootstrap_resource_group_${locals.environment}"
  location = locals.location
}
