import os
import asyncio
import discord
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.infrastructure.config.settings import load_environment, Settings
from src.infrastructure.database.models import Base
from src.infrastructure.notion_client.client import NotionClient
from src.infrastructure.discord_client.client import DiscordClient
from src.domain.notion.repositories import SQLNotionRepository
from src.application.notion.notion_service import NotionService
from src.application.discord.discord_service import DiscordService
from src.utils.logging import logger


async def setup_discord_service(
    settings: Settings, session_factory
) -> tuple[DiscordService, DiscordClient]:
    """Setup Discord service and client"""
    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    notion_client = NotionClient(settings.NOTION_TOKEN, settings.NOTION_DATABASE_ID)
    notion_repository = SQLNotionRepository(session_factory)

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

    intents = discord.Intents.default()
    intents.message_content = True

    discord_client = DiscordClient(
        discord_service=discord_service, settings=settings, intents=intents
    )

    return discord_service, discord_client


async def main():
    """Main entry point"""
    try:
        settings = load_environment()

        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        discord_service, discord_client = await setup_discord_service(
            settings, async_session
        )

        await discord_client.start(settings.DISCORD_BOT_TOKEN)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
