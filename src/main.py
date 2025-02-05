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

async def init_database(settings: Settings):
    """Initialize database connection and create tables"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_services(settings: Settings, async_session: sessionmaker):
    """Initialize all services with dependencies"""
    # Create Notion client
    notion_client = NotionClient(
        auth_token=settings.NOTION_TOKEN,
        database_id=settings.NOTION_DATABASE_ID
    )
    
    # Create repository with database session
    async with async_session() as session:
        notion_repository = SQLNotionRepository(session)
    
    # Create Notion service
    notion_service = NotionService(
        notion_client=notion_client,
        notion_repository=notion_repository,
        notification_channels=settings.NOTION_NOTIFICATION_CHANNELS
    )
    
    # Create Discord service
    discord_service = DiscordService(
        notion_service=notion_service,
        settings=settings,
        check_interval=settings.UPDATE_INTERVAL
    )
    
    return discord_service

async def main():
    try:
        settings = load_environment()
        async_session = await init_database(settings)
        discord_service = await init_services(settings, async_session)
        
        # Initialize database
        await discord_service.initialize()
        
        # Start the Discord client
        await discord_service.client.start(settings.DISCORD_BOT_TOKEN)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
