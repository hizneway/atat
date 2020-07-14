module "keyvault_reader_identity" {
  source      = "../../modules/managed_identity"
  name        = var.name
  owner       = var.owner
  environment = var.environment
  region      = var.region
  identity    = "${var.name}-${var.environment}-vault-reader"
  roles       = ["Reader", "Managed Identity Operator"] # Scope on these is subscription wide, should be least.

}


module "keyvault_reader_identity_private_k8s" {
  source      = "../../modules/managed_identity"
  name        = var.name
  owner       = var.owner
  environment = var.environment
  region      = var.region
  identity    = "${var.name}-${var.environment}-private-k8s"
  roles       = ["Reader", "Managed Identity Operator"] # Scope on these is subscription wide, should be least.

}
