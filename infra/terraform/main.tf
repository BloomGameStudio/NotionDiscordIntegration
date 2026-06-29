terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  backend "local" {}
}

provider "azurerm" {
  features {}
}

locals {
  is_staging          = var.environment == "staging"
  env_prefix          = local.is_staging ? "stg-" : ""
  resource_group_name = format("rg-%s%s-%s-%s", local.env_prefix, var.workload_name, var.location_short, var.instance)
  function_app_name   = format("fa-%s%s-%s-%s", local.env_prefix, var.workload_name, var.location_short, var.instance)
}

module "function_app" {
  source = "./modules/function_app"

  project_name                 = var.project_name
  environment                  = var.environment
  location                     = var.location
  resource_group_name          = local.resource_group_name
  function_app_name            = local.function_app_name
  sync_cron                    = var.sync_cron
  notion_token                 = var.notion_token
  notion_database_id           = var.notion_database_id
  discord_bot_token            = var.discord_bot_token
  notion_notification_channels = var.notion_notification_channels
  storage_table_name           = var.storage_table_name

  tags = merge(var.tags, {
    environment = var.environment
  })
}
