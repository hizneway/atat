# Goals

- [ ] Move to the new subscription

- [ ] Bump the provider version
- [ ] Implement 'plan' for the big terraform
- [ ] Figure out why 'rattler' is being referenced
- [ ] Figure out what's wrong w/ the terraform cli invocation right now
- [ ] terraform failed because of a forbidden by firewall issue
Error: Error checking for presence of existing Key "SECRET-KEY" (Key Vault "https://cz-kv-lobster.vault.azure.net/"): keyvault.BaseClient#GetKey: Failure responding to request: StatusCode=403 -- Original Error: autorest/azure: Service returned an error. Status=403 Code="Forbidden" Message="Client address is not authorized and caller is not a trusted service.\r\nClient address: 96.245.77.154\r\nCaller: appid=353b99ef-3dc3-4654-8f91-2adce7ef6464;oid=799619c8-eaa3-4e10-b4e3-50a60cb98532;iss=https://sts.windows.net/b5ab0e1e-09f8-4258-afb7-fb17654bc5b3/\r\nVault: cz-kv-lobster;location=eastus" InnerError={"code":"ForbiddenByFirewall"}

  on ../../modules/keyvault/main.tf line 111, in resource "azurerm_key_vault_key" "generated":
 111: resource "azurerm_key_vault_key" "generated" {
