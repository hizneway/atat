output "k8s_resource_group_id" {
  value = azurerm_kubernetes_cluster.k8s_private.node_resource_group
}

output "k8s_resource_group_name" {
  value = "${var.rg}-private-aks-node-rgs"
}
