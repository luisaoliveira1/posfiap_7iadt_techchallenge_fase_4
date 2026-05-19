variable "environment" {
  type        = string
  default     = "dev"
  description = "Deployment environment"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod."
  }
}

variable "location" {
  type        = string
  default     = "eastus"
  description = "Azure region."
}

variable "project" {
  type    = string
  default = "ppd"
}
