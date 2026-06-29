resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  base_name            = substr(replace("${var.project_name}${var.environment}", "-", ""), 0, 12)
  storage_account_name = substr("${local.base_name}${random_string.suffix.result}", 0, 24)
}

resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

resource "azurerm_storage_account" "this" {
  name                     = local.storage_account_name
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"

  tags = var.tags
}

resource "azurerm_service_plan" "this" {
  name                = "${var.project_name}-${var.environment}-asp"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  os_type             = "Linux"
  sku_name            = "Y1"

  tags = var.tags
}

resource "azurerm_linux_function_app" "this" {
  name                = var.function_app_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  service_plan_id            = azurerm_service_plan.this.id
  storage_account_name       = azurerm_storage_account.this.name
  storage_account_access_key = azurerm_storage_account.this.primary_access_key

  functions_extension_version = "~4"
  https_only                  = true

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME              = "python"
    WEBSITE_RUN_FROM_PACKAGE              = "1"
    AzureWebJobsStorage                   = azurerm_storage_account.this.primary_connection_string
    SYNC_CRON                             = var.sync_cron
    NOTION_TOKEN                          = var.notion_token
    NOTION_DATABASE_ID                    = var.notion_database_id
    DISCORD_BOT_TOKEN                     = var.discord_bot_token
    NOTION_NOTIFICATION_CHANNELS          = var.notion_notification_channels
    STORAGE_TABLE_NAME                    = var.storage_table_name
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}
