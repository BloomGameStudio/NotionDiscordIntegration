import asyncio
import discord
from src.infrastructure.config.database import engine, SessionLocal
from src.infrastructure.config.settings import load_environment, Settings
from src.infrastructure.notion_client.client import NotionClient
from src.infrastructure.discord_client.client import DiscordClient
from src.domain.notion.repositories import SQLNotionRepository
from src.application.notion.notion_service import NotionService
from src.application.discord.discord_service import DiscordService
from src.scripts.init_db import init_db


def setup_discord_service(
    settings: Settings,
) -> tuple[DiscordService, DiscordClient]:
    """Setup Discord service and client"""

    notion_client = NotionClient(settings.NOTION_TOKEN, settings.NOTION_DATABASE_ID)
    notion_repository = SQLNotionRepository(SessionLocal)

    intents = discord.Intents.default()
    intents.message_content = True

    notion_service = NotionService(
        notion_client=notion_client,
        notion_repository=notion_repository,
        notification_channels=settings.NOTION_NOTIFICATION_CHANNELS,
        update_cooldown=settings.UPDATE_COOLDOWN,
    )

    discord_service = DiscordService(
        notion_service=notion_service,
        settings=settings,
        check_interval=settings.UPDATE_INTERVAL,
    )

    discord_client = DiscordClient(
        discord_service=discord_service, settings=settings, intents=intents
    )

    # Set the client reference in the service
    discord_service.client = discord_client

    return discord_service, discord_client


async def main():
    try:
        settings = load_environment()
        init_db()

        discord_service, discord_client = setup_discord_service(settings)

        await discord_client.start(settings.DISCORD_BOT_TOKEN)

        await discord_client.wait_until_ready()
        await asyncio.Future()

    except Exception as e:
        print(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
