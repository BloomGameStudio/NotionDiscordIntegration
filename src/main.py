import asyncio
from src.infrastructure.config.settings import load_environment, Settings
from src.infrastructure.notion_client.client import NotionClient
from src.infrastructure.discord_client.rest_client import DiscordRestClient
from src.domain.notion.repositories import TableStorageNotionRepository
from src.application.notion.notion_service import NotionService
from src.utils.logging import logger


def setup_notion_service(settings: Settings) -> NotionService:
    notion_client = NotionClient(settings.NOTION_TOKEN, settings.NOTION_DATABASE_ID)
    notion_repository = TableStorageNotionRepository(
        settings.STORAGE_CONNECTION_STRING,
        settings.STORAGE_TABLE_NAME,
    )

    return NotionService(
        notion_client=notion_client,
        notion_repository=notion_repository,
        notification_channels=settings.NOTION_NOTIFICATION_CHANNELS,
        update_cooldown=settings.UPDATE_COOLDOWN,
    )


async def run_scheduled_sync(settings: Settings) -> None:
    """Run exactly one sync cycle for serverless/cron execution."""
    notion_service = setup_notion_service(settings)

    creation_notifications = await notion_service.handle_creations()
    update_notifications = await notion_service.handle_updates()
    notifications = creation_notifications + update_notifications

    if not notifications:
        logger.info("Scheduled sync completed: no new notifications")
        return

    async with DiscordRestClient(settings.DISCORD_BOT_TOKEN) as discord_client:
        for notification in notifications:
            message = f"**{notification.title}**\n{notification.content}"
            for channel_id in notification.channels:
                await discord_client.send_message(channel_id, message)

    logger.info(
        "Scheduled sync completed: sent %s notifications", len(notifications)
    )


async def main():
    """Main entry point for one-shot scheduled sync."""
    try:
        settings = load_environment()
        await run_scheduled_sync(settings)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
