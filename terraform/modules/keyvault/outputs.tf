output "id" {
  value = azurerm_key_vault.keyvault.id
}

output "url" {
  value = azurerm_key_vault.keyvault.vault_uri
}

output "keyvault_name" {
  value = "${var.name}-kv-${var.environment}"
}

output "keyvault_spun_up" {
  value = { }
  depends_on = [ time_sleep.wait_30_seconds ]
}
