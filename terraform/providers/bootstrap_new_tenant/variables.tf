variable "namespace" {
  type        = string
  default     = "dev"
  description = "Namespace of provisioned resources."
}

variable "location" {
  type        = string
  default     = "East US"
  description = "Azure region in which resources are provisioned."
}
