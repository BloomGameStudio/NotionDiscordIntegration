<div align="center">

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

</div>

# Notion/Discord Integration

A Discord bot that integrates with Notion for updates and notifications.

### Schedule

Set `SYNC_CRON` in Function App settings. The default is every 4 hours:

```text
0 0 */4 * * *
```

### Required App Settings

- `NOTION_TOKEN`
- `NOTION_DATABASE_ID`
- `DISCORD_BOT_TOKEN`
- `NOTION_NOTIFICATION_CHANNELS`
- `DATABASE_URL`
- `SYNC_CRON`

For local development, copy `local.settings.sample.json` to `local.settings.json` and fill in values.

## Terraform Deployment

Terraform definitions are in:

- `infra/terraform/modules/function_app`
- `infra/terraform`

Each environment provisions:

- Resource Group
- Storage Account
- App Service Plan (Y1 / Consumption)
- Application Insights
- Linux Function App (Python 3.11)

### Naming Convention

Terraform generates names from `TF_VAR_environment`:

- Staging: `rg-stg-<workload_name>-<location_short>-<instance>`
- Prod: `rg-<workload_name>-<location_short>-<instance>`

Function App names follow:

- Staging: `fa-stg-<workload_name>-<location_short>-<instance>`
- Prod: `fa-<workload_name>-<location_short>-<instance>`

Defaults are set to produce:

- `rg-stg-websitev1-eus-01`
- `rg-websitev1-eus-01`

### Terraform State Backend

The root uses the `local` backend.

For local development, initialize Terraform with an environment-specific state file:

```bash
terraform -chdir=infra/terraform init \
	-backend-config="path=terraform-staging.tfstate"
```

For production, use `terraform-prod.tfstate`.

### Manual Apply Example

```bash
export TF_VAR_environment="staging"
export TF_VAR_notion_token="..."
export TF_VAR_notion_database_id="..."
export TF_VAR_discord_bot_token="..."
export TF_VAR_notion_notification_channels="1234567890"
export TF_VAR_database_url="..."
export TF_VAR_sync_cron="0 0 */4 * * *"

terraform -chdir=infra/terraform apply
```

## GitHub CI/CD

Workflow: `.github/workflows/deploy-function-app.yml`

- Push to `dev` deploys dev.
- Push to `main` deploys prd.
- `workflow_dispatch` supports manual environment selection.

Create GitHub Environments named `dev` and `prd` and configure these environment secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `NOTION_TOKEN`
- `NOTION_DATABASE_ID`
- `DISCORD_BOT_TOKEN`
- `NOTION_NOTIFICATION_CHANNELS`
- `DATABASE_URL`

Optional environment variable:

- `SYNC_CRON` (GitHub Environment variable, defaults to `0 0 */4 * * *` if unset)

## Setup
Make copy of the environment variables file and fill in appropriate values:
```bash
cp .env.example .env
```

## Run

### Azure Functions Local

1. Install Azure Functions Core Tools.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start Functions host:

```bash
func start
```

## Run Scripts
**Double check your environment variables are set to target the correct database.**

Activate the virtual environment:
```bash
pipenv shell
```

### Initialize database
```bash
python -m src.scripts.init_db
```

### Run query
```bash
python -m src.scripts.query
```
