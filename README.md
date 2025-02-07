# NotionDiscordIntegration

A Discord bot that integrates with Notion for updates and notifications.

## Setup

1. Clone the repository or copy the necessary files:
   ```bash
   git clone https://github.com/BloomGameStudio/NotionDiscordIntegration.git
   ```

2. Create and configure the environment variables:
   - Copy `.env.example` to `.env`
   - Fill in the required values:
     ```
     DISCORD_BOT_TOKEN=your_discord_bot_token
     NOTION_TOKEN=your_notion_token
     DB_PASSWORD=your_database_password
     NOTION_DATABASE_ID=your_notion_database_id
     NOTION_NOTIFICATION_CHANNELS=channel_id1,channel_id2
     ```

## Deployment Options

### Docker (Recommended for Production)

1. Make sure Docker and Docker Compose are installed on your system

2. Start the containers:
   ```bash
   docker-compose up -d
   ```

3. Check the logs:
   ```bash
   docker-compose logs -f bot
   ```

### Heroku

1. Install the Heroku CLI and login:
   ```bash
   heroku login
   ```

2. Create a new Heroku app:
   ```bash
   heroku create your-app-name
   ```

3. Add the Heroku Postgres addon:
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

4. Configure environment variables:
   ```bash
   heroku config:set DISCORD_BOT_TOKEN=your_discord_bot_token
   heroku config:set NOTION_TOKEN=your_notion_token
   heroku config:set NOTION_DATABASE_ID=your_notion_database_id
   heroku config:set NOTION_NOTIFICATION_CHANNELS=channel_id1,channel_id2
   ```

5. Deploy to Heroku:
   ```bash
   git push heroku main
   ```

6. Ensure the worker is running:
   ```bash
   heroku ps:scale worker=1
   ```

### Local Development

1. Install dependencies:
   ```bash
   pip install pipenv
   pipenv install --dev
   ```

2. Run the bot:
   ```bash
   heroku local
   ```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DISCORD_BOT_TOKEN` | Discord Bot Token | Yes | - |
| `NOTION_TOKEN` | Notion Integration Token | Yes | - |
| `DB_PASSWORD` | Database Password | Yes | - |
| `NOTION_DATABASE_ID` | Notion Database ID | No | Default in settings |
| `NOTION_NOTIFICATION_CHANNELS` | Discord Channel IDs | No | Default in constants |
| `DATABASE_URL` | Full Database URL | No | Constructed from other vars |

## Database Migrations

### Migrating Data to Heroku

If you need to migrate existing data to a new Heroku deployment:

1. Ensure your local Postgres database is running:
   ```bash
   docker-compose up -d db
   ```

2. Verify your environment variables are set:
   ```bash
   # Local database connection
   export DATABASE_URL=postgresql+asyncpg://notion_bot:your_local_password@localhost:5432/notion_bot
   ```

3. Run the migration script:
   ```bash
   # Activate the virtual environment
   pipenv shell
   
   # Run the migration
   python -m src.scripts.migrate
   ```

4. Verify the migration:
   ```bash
   python -m src.scripts.query
   ```
## License

[MIT License](LICENSE)
