module "container_registry" {
  source        = "../../modules/container_registry"
  name          = var.name
  region        = var.region
  environment   = var.environment
  owner         = var.owner
  backup_region = var.backup_region
  policy        = "Allow"
  subnet_ids    = [module.vpc.subnet_list["aks"].id]
  whitelist     = var.admin_user_whitelist
  workspace_id  = module.logs.workspace_id
}