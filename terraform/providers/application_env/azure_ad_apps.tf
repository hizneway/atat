module "tenant_keyvault_app" {
  source      = "../../modules/azure_ad"
  name        = "tenant-keyvault-${local.environment}"
  environment = local.environment
}


module "aks_sp" {
  source      = "../../modules/azure_ad"
  name        = "aks-service-principal-${local.environment}"
  environment = local.environment
}

module "bastion_sp" {
  source      = "../../modules/azure_ad"
  name        = "bastion-service-principal-${local.environment}"
  environment = local.environment
}

module "ops_keyvault_app" {
  source      = "../../modules/azure_ad"
  name        = "ops-keyvault-sp-${local.environment}"
  environment = local.environment
}
