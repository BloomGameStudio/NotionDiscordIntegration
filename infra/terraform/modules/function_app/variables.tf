variable "project_name" {
  description = "Project/application name prefix"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "function_app_name" {
  description = "Azure Function App name"
  type        = string
}

variable "sync_cron" {
  description = "Timer trigger schedule"
  type        = string
  default     = "0 0 */4 * * *"
}

variable "notion_token" {
  description = "Notion integration token"
  type        = string
  sensitive   = true
}

variable "notion_database_id" {
  description = "Notion database ID"
  type        = string
}

variable "discord_bot_token" {
  description = "Discord bot token"
  type        = string
  sensitive   = true
}

variable "notion_notification_channels" {
  description = "Comma-separated list of Discord channel IDs"
  type        = string
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
