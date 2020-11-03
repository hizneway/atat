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

# Specifying a `provider` this way is deprecated. It is necessary in this 
# situation due to an issue with the `azurerm` provider. 
#
# https://www.terraform.io/docs/configuration/providers.html#version-an-older-way-to-manage-provider-versions
# https://github.com/terraform-providers/terraform-provider-azurerm/issues/7359
provider "azurerm" {
  features {}
}

variable "namespace" {
  type        = string
  default     = "dev"
  description = "Namespace of provisioned resources."
}

variable "location" {
  type        = string
  default     = "East US"
  description = "Azure region in which resources are provisioned."
}

resource "azurerm_resource_group" "bootstrap_resource_group" {
  name     = "cloudzero-ops-${var.namespace}"
  location = var.location
}

resource "azurerm_virtual_network" "bootstrap_virtual_network" {
  name                = "cloudzero-ops-network-${var.namespace}"
  location            = var.location
  resource_group_name = azurerm_resource_group.bootstrap_resource_group.name
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "deployment_subnet" {
  name                 = "deployment-subnet-${var.namespace}"
  address_prefixes     = ["10.0.1.0/24"]
  resource_group_name  = azurerm_resource_group.bootstrap_resource_group.name
  virtual_network_name = azurerm_virtual_network.bootstrap_virtual_network.name

  service_endpoints = [
    "Microsoft.ContainerRegistry",
    "Microsoft.KeyVault",
    "Microsoft.Sql",
    "Microsoft.Storage"
  ]
}

resource "azurerm_storage_account" "bootstrap_storage_account" {
  name                     = "czopsstorageaccount${var.namespace}"
  resource_group_name      = azurerm_resource_group.bootstrap_resource_group.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  network_rules {
    default_action             = "Deny"
    virtual_network_subnet_ids = [azurerm_subnet.deployment_subnet.id]
  }
}

resource "azurerm_container_registry" "bootstrap_container_registry" {
  name                = "cloudzeroopsregistry${var.namespace}"
  resource_group_name = azurerm_resource_group.bootstrap_resource_group.name
  location            = var.location
  sku                 = "Premium"
}
