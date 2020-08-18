provider "azurerm" {
  version         = "=2.0.0"
  subscription_id = "95934d54-980d-47cc-9bce-3a96bf9a2d1b"
  features {}
}

provider "azuread" {
  # Whilst version is optional, we /strongly recommend/ using it to pin the version of the Provider being used
  version = "=0.7.0"
}

# (Just for reference) this terraform config requires a partial config https://www.terraform.io/docs/backends/config.html
terraform {}
