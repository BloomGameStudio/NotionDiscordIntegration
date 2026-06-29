variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["staging", "prod"], var.environment)
    error_message = "environment must be one of: staging, prod"
  }
}

variable "project_name" {
  type    = string
  default = "notion-discord"
}

variable "workload_name" {
  type    = string
  default = "notion-discord"
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "location_short" {
  type    = string
  default = "eus"
}

variable "instance" {
  type    = string
  default = "01"
}

variable "sync_cron" {
  type    = string
  default = "0 0 */4 * * *"
}

variable "notion_token" {
  type      = string
  sensitive = true
}

variable "notion_database_id" {
  type = string
}

variable "discord_bot_token" {
  type      = string
  sensitive = true
}

variable "notion_notification_channels" {
  type = string
}

variable "storage_table_name" {
  type    = string
  default = "notionDocuments"
}

variable "tags" {
  type = map(string)
  default = {
    workload = "notion-discord-integration"
    managed  = "terraform"
  }
}
