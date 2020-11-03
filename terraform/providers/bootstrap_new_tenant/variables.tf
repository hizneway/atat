variable "operations_location" {
  type        = string
  default     = "East US"
  description = "Azure region in which operations resources are provisioned."
}

variable "operations_namespace" {
  type        = string
  default     = "dev"
  description = "Namespace of provisioned operations resources."
}
