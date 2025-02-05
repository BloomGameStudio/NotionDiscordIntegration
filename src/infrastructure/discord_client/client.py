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
        self,
        discord_service: DiscordService,
        settings: Settings,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.discord_service = discord_service
        self.settings = settings
        self.tree = app_commands.CommandTree(self)
        self.check_updates.start()

    async def setup_hook(self) -> None:
        """Set up background tasks when the bot starts"""
        # Initialize services
        await self.discord_service.initialize()
        
        # Start notification task
        self.bg_task = self.loop.create_task(self._run_notification_loop())
        
        logger.info("Discord client setup completed")

    async def _run_notification_loop(self) -> None:
        """Main notification processing loop"""
        await self.wait_until_ready()
        
        async for notification in self.discord_service.start_notification_tasks():
            for channel_id in notification.channels:
                channel = self.get_channel(channel_id)
                if channel:
                    try:
                        message = self.discord_service.format_notification(notification)
                        await channel.send(message)
                    except Exception as e:
                        logger.error(f"Error sending message to channel {channel_id}: {e}")

    async def on_ready(self) -> None:
        """Called when the bot is ready"""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # Register notification channels
        for channel_id in self.settings.NOTION_NOTIFICATION_CHANNELS:
            channel = self.get_channel(channel_id)
            if channel:
                self.discord_service.register_channel(channel_id)
            else:
                logger.warning(f"Could not find channel with ID: {channel_id}")

    @tasks.loop(minutes=2)
    async def check_updates(self):
        """Check for updates every 2 minutes"""
        try:
            # Check for new documents
            creation_notifications = await self.discord_service.handle_creation_notifications()
            for notification in creation_notifications:
                for channel_id in notification.channels:
                    channel = self.get_channel(channel_id)
                    if channel:
                        await channel.send(notification.content)

            # Check for updates
            update_notifications = await self.discord_service.handle_update_notifications()
            for notification in update_notifications:
                for channel_id in notification.channels:
                    channel = self.get_channel(channel_id)
                    if channel:
                        await channel.send(notification.content)

            # Check for weekly summary
            aggregate_notification = await self.discord_service.handle_aggregate_updates()
            if aggregate_notification:
                for channel_id in aggregate_notification.channels:
                    channel = self.get_channel(channel_id)
                    if channel:
                        await channel.send(aggregate_notification.content)

        except Exception as e:
            logger.error(f"Error checking updates: {e}") 