output "database_name" {
  value = azurerm_postgresql_database.db.name
}

output "postgres_resource_group_name" {
  value = azurerm_resource_group.sql.name
}

output "admin_name" {
  value = var.administrator_login
}

output "pg_admin_user" {
  value = azurerm_postgresql_server.sql.administrator_login
}

output "pgpassword" {
  value = azurerm_postgresql_server.sql.administrator_login_password
}

output "fqdn" {
  value = azurerm_postgresql_server.sql.fqdn
}

output "app_user" {
  value = "atat@${var.name}-sql-${var.environment}"
}
