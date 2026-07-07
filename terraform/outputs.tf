output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "location" {
  value = azurerm_resource_group.main.location
}

output "load_balancer_public_ip" {
  value = azurerm_public_ip.lb.ip_address
}

output "vmss_name" {
  value = azurerm_linux_virtual_machine_scale_set.app.name
}

output "vmss_resource_id" {
  value = azurerm_linux_virtual_machine_scale_set.app.id
}

output "current_instance_count" {
  value = azurerm_linux_virtual_machine_scale_set.app.instances
}