import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import discord
from discord.ext import commands, tasks
from src.application.notion.notion_service import NotionService
from src.application.notion.dto import NotificationMessage
from src.infrastructure.config.settings import Settings
from src.utils.logging import logger

class DiscordService:
    def __init__(
        self,
        notion_service: NotionService,
        settings: Settings,
        check_interval: int = 120
    ):
        self.notion_service = notion_service
        self.settings = settings
        self.connected_channels: List[int] = []
        self._start_time = datetime.now(timezone.utc)
        self._last_heartbeat = datetime.utcnow()
        self._db_lock = asyncio.Lock()
        self.check_interval = check_interval
        
        # Create Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        @self.client.event
        async def on_ready():
            logger.info(f'Bot is ready as {self.client.user}')
            
            # Register notification channels
            for channel_id in self.settings.NOTION_NOTIFICATION_CHANNELS:
                channel = self.client.get_channel(channel_id)
                if channel:
                    self.register_channel(channel_id)
                else:
                    logger.warning(f"Could not find channel with ID: {channel_id}")
            
            # Setup and start periodic tasks
            self._setup_periodic_tasks()
            await self.start()
        
    def _setup_periodic_tasks(self):
        @tasks.loop(seconds=120)
        async def check_updates():
            logger.info("Checking for document updates...")
            notifications = await self.handle_update_notifications()
            logger.info(f"Found {len(notifications)} updates")
            for notification in notifications:
                await self._send_notification(notification)

        @tasks.loop(seconds=120)
        async def check_creations():
            logger.info("Checking for new documents...")
            notifications = await self.handle_creation_notifications()
            logger.info(f"Found {len(notifications)} new documents")
            for notification in notifications:
                await self._send_notification(notification)

        @tasks.loop(hours=24)
        async def check_weekly_updates():
            logger.info("Checking for weekly updates...")
            notification = await self.handle_aggregate_updates()
            if notification:
                logger.info("Sending weekly update summary")
                await self._send_notification(notification)

        self.check_updates = check_updates
        self.check_creations = check_creations
        self.check_weekly_updates = check_weekly_updates

    def register_channel(self, channel_id: int) -> None:
        """Register a Discord channel for notifications"""
        if channel_id not in self.connected_channels:
            self.connected_channels.append(channel_id)
            logger.info(f"Registered channel: {channel_id}")

    async def initialize(self) -> None:
        """Initialize service and perform initial database sync"""
        try:
            async with self._db_lock:
                await self.notion_service.sync_db()
            logger.info("Initial database sync completed")
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            raise

    async def handle_creation_notifications(self) -> List[NotificationMessage]:
        """Handle notifications for newly created documents"""
        try:
            async with self._db_lock:
                return await self.notion_service.handle_creations()
        except Exception as e:
            logger.error(f"Error handling creation notifications: {e}")
            return []

    async def handle_update_notifications(self) -> List[NotificationMessage]:
        """Handle notifications for updated documents"""
        try:
            async with self._db_lock:
                return await self.notion_service.handle_updates()
        except Exception as e:
            logger.error(f"Error handling update notifications: {e}")
            return []

    async def handle_aggregate_updates(self) -> Optional[NotificationMessage]:
        """Handle weekly aggregate updates"""
        try:
            current_time = datetime.now(timezone.utc)  # Make timezone-aware
            time_difference = current_time - self._start_time
            
            if time_difference.days >= 7:
                async with self._db_lock:
                    notification = await self.notion_service.handle_aggregate_updates(
                        start_time=self._start_time
                    )
                
                if notification:
                    self._start_time = current_time
                    return notification
            
            return None
        except Exception as e:
            logger.error(f"Error handling aggregate updates: {e}")
            return None

    def format_notification(self, notification: NotificationMessage) -> str:
        """Format notification for Discord message"""
        return f"{notification.title}\n{notification.content}"

    async def start_notification_tasks(self) -> None:
        """Start all notification tasks"""
        while True:
            try:
                creation_notifications = await self.handle_creation_notifications()
                for notification in creation_notifications:
                    yield notification

                update_notifications = await self.handle_update_notifications()
                for notification in update_notifications:
                    yield notification

                aggregate_notification = await self.handle_aggregate_updates()
                if aggregate_notification:
                    yield aggregate_notification

                self._last_heartbeat = datetime.utcnow()
                
                await asyncio.sleep(self.settings.UPDATE_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in notification tasks: {e}")
                await asyncio.sleep(self.settings.UPDATE_INTERVAL)

    def get_bot_state(self) -> dict:
        """Get current bot state"""
        return {
            "start_time": self._start_time.isoformat(),
            "last_heartbeat": self._last_heartbeat.isoformat(),
            "connected_channels": self.connected_channels,
            "uptime": str(datetime.utcnow() - self._start_time)
        }

    @tasks.loop(minutes=5)
    async def check_updates(self):
        """Check for Notion updates periodically"""
        try:
            notifications = await self.notion_service.handle_updates()
            for notification in notifications:
                for channel_id in notification.channels:
                    channel = self.client.get_channel(channel_id)
                    if channel:
                        await channel.send(
                            content=notification.content,
                            embed=notification.to_discord_embed()
                        )
        except Exception as e:
            logger.error(f"Error checking updates: {e}")

    async def start(self) -> None:
        """Start the periodic tasks"""
        self.check_updates.start()
        self.check_creations.start()
        self.check_weekly_updates.start()

    async def _send_notification(self, notification: NotificationMessage):
        """Send a notification to all connected channels"""
        for channel_id in self.connected_channels:
            channel = self.client.get_channel(channel_id)
            if channel:
                await channel.send(
                    content=notification.content,
                    embed=notification.to_discord_embed()
                ) 