import discord
from discord import app_commands
from discord.ext import tasks
from datetime import datetime, timezone
from src.application.discord.discord_service import DiscordService
from src.infrastructure.config.settings import Settings
from src.utils.logging import logger


def initialize_discord_client() -> discord.Client:
    intents = discord.Intents.default()
    client = DiscordClient(intents=intents)
    return client


class DiscordClient(discord.Client):
    def __init__(
        self, discord_service: DiscordService, settings: Settings, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.settings = settings
        self.tree = app_commands.CommandTree(self)
        discord_service.client = self
        self.discord_service = discord_service

    async def setup_hook(self) -> None:
        """Set up background tasks when the bot starts"""
        logger.info("Setting up Discord client...")
        self.check_updates.start()
        logger.info("Started check_updates task")
        logger.info("Discord client setup completed")

    async def on_ready(self) -> None:
        """Called when the bot is ready"""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

        for channel_id in self.settings.NOTION_NOTIFICATION_CHANNELS:
            channel = self.get_channel(channel_id)
            if channel:
                self.discord_service.register_channel(channel_id)
                logger.info(f"Successfully registered channel: {channel_id}")
            else:
                logger.warning(f"Could not find channel with ID: {channel_id}")

        if self.discord_service.connected_channels:
            await self.discord_service.initialize()
        else:
            logger.error(
                "No channels were registered successfully. Cannot initialize service."
            )

    @tasks.loop(minutes=2)
    async def check_updates(self):
        """Check for updates every 2 minutes"""
        try:
            logger.info("Starting periodic update check...")

            creation_notifications = (
                await self.discord_service.handle_creation_notifications()
            )
            logger.info(f"Found {len(creation_notifications)} new documents")
            for notification in creation_notifications:
                await self.discord_service._send_notification(notification)

            update_notifications = (
                await self.discord_service.handle_update_notifications()
            )
            logger.info(f"Found {len(update_notifications)} updates")
            for notification in update_notifications:
                await self.discord_service._send_notification(notification)

            aggregate_notification = (
                await self.discord_service.handle_aggregate_updates()
            )
            if aggregate_notification:
                logger.info("Sending weekly summary")
                await self.discord_service._send_notification(aggregate_notification)

            logger.info("Completed periodic update check")
        except Exception as e:
            logger.error(f"Error in check_updates task: {e}", exc_info=True)

    @check_updates.before_loop
    async def before_check_updates(self):
        """Wait until the bot is ready before starting the task"""
        logger.info("Waiting for bot to be ready before starting check_updates task...")
        await self.wait_until_ready()
        logger.info("Bot is ready, starting check_updates task")
