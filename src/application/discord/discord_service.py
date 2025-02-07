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
        client: discord.Client = None,
        check_interval: int = 120
    ):
        self.notion_service = notion_service
        self.settings = settings
        self.client = client
        self.connected_channels: List[int] = []
        self._start_time = datetime.now(timezone.utc)
        self._last_heartbeat = datetime.utcnow()
        self._db_lock = asyncio.Lock()
        self.check_interval = check_interval

    def _setup_periodic_tasks(self):
        """This method should be removed as task scheduling is handled by DiscordClient"""
        pass

    def register_channel(self, channel_id: int) -> None:
        """Register a Discord channel for notifications"""
        if channel_id not in self.connected_channels:
            self.connected_channels.append(channel_id)
            logger.info(f"Registered channel: {channel_id}")

    async def initialize(self) -> None:
        """Initialize service"""
        try:
            if not self.client.is_ready():
                logger.info("Waiting for Discord client to be ready...")
                await self.client.wait_until_ready()
            
            for channel_id in self.notion_service.notification_channels:
                self.register_channel(channel_id)
                logger.info(f"Pre-registered channel: {channel_id}")
            
            logger.info("Discord service initialization completed")
        except Exception as e:
            logger.error(f"Error during initialization: {e}", exc_info=True)
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
            current_time = datetime.now(timezone.utc)
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

    async def _send_notification(self, notification: NotificationMessage):
        """Send a notification to all connected channels"""
        logger.debug(f"Attempting to send notification to channels: {self.connected_channels}")
        if not self.connected_channels:
            logger.warning("No channels registered to receive notifications")
            return
        
        formatted_message = f"**{notification.title}**\n{notification.content}"
        
        for channel_id in self.connected_channels:
            channel = self.client.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(content=formatted_message)
                    logger.info(f"Successfully sent notification to channel {channel_id}")
                except Exception as e:
                    logger.error(f"Error sending message to channel {channel_id}: {e}")
            else:
                logger.warning(f"Could not find channel with ID: {channel_id}")

    async def send_message(self, channel_id: int, title: str, content: str):
        """Send a message to a specific channel"""
        channel = self.client.get_channel(channel_id)
        if channel:
            try:
                message = f"**{title}**\n{content}"
                await channel.send(content=message)
                logger.info(f"Successfully sent message to channel {channel_id}")
            except Exception as e:
                logger.error(f"Error sending message to channel {channel_id}: {e}")
        else:
            logger.warning(f"Could not find channel with ID: {channel_id}") 