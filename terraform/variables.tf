variable "project_name" {
  type    = string
  default = "selfhealing"
}

variable "resource_group_name" {
  type    = string
  default = "rg-selfhealing-network"
}

variable "location" {
  type    = string
  default = "UAE North"
}

variable "vm_sku" {
  type    = string
  default = "Standard_D2s_v3"
}

variable "instance_count" {
  type    = number
  default = 1
}

variable "admin_username" {
  type = string
}

variable "admin_password" {
  type      = string
  sensitive = true
}