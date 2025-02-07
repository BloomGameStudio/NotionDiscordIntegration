from datetime import datetime, timedelta, timezone
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.application.discord.discord_service import DiscordService

from src.domain.notion.entities import NotionDocument
from src.domain.notion.repositories import NotionRepository
from src.infrastructure.notion_client.client import NotionClient
from .dto import NotificationMessage
from src.utils.logging import logger
from src.infrastructure.config.constants import MESSAGE_TEMPLATES

class NotionService:
    def __init__(
        self,
        notion_client: NotionClient,
        notion_repository: NotionRepository,
        notification_channels: List[int],
        update_cooldown: int = 14400  # 4 hours default
    ):
        self.notion_client = notion_client
        self.notion_repository = notion_repository
        self.notification_channels = notification_channels
        self._last_update_times = {}
        self.update_cooldown = update_cooldown

    async def _get_user_safely(self, user_id: str) -> str:
        """Safely get user information with fallback"""
        try:
            user = await self.notion_client.get_user(user_id)
            return user
        except Exception as e:
            logger.warning(f"Could not fetch user info for {user_id}: {e}")
            return "Unknown User"

    async def handle_creations(self) -> List[NotificationMessage]:
        """Handle notifications for newly created documents"""
        try:
            documents = await self.notion_client.get_recent_documents()
            notifications = []
            
            for doc in documents:
                existing_doc = await self.notion_repository.get_document(doc.id)
                if not existing_doc:
                    title = doc.title[0]['plain_text'] if isinstance(doc.title, list) else doc.title
                    doc.title = title  # Update the document title
                    
                    logger.info(f"Saving new document to database: {title}")
                    await self.notion_repository.save_document(doc)
                    
                    created_by = await self._get_user_safely(doc.created_by.id)
                    logger.info(f"Creating notification for new document: {title}")
                    
                    notifications.append(NotificationMessage(
                        title=MESSAGE_TEMPLATES["creation"].format(doc.title),
                        content=self._format_creation_message(doc, created_by),
                        timestamp=doc.created_time,
                        channels=self.notification_channels
                    ))

            return notifications
        except Exception as e:
            logger.error(f"Error handling creations: {e}")
            return []

    async def handle_updates(self) -> List[NotificationMessage]:
        """Handle notifications for updated documents"""
        try:
            documents = await self.notion_client.get_updated_documents()
            logger.info(f"Processing {len(documents)} potential updates")
            notifications = []
            current_time = datetime.now(timezone.utc)
            
            for doc in documents:
                title = doc.title[0]['plain_text'] if isinstance(doc.title, list) else doc.title
                doc.title = title
                
                if doc.id in self._last_update_times:
                    last_update = self._last_update_times[doc.id]
                    time_since_last_update = (current_time - last_update).total_seconds()
                    if time_since_last_update < self.update_cooldown:
                        logger.debug(f"Skipping update for {title} due to cooldown")
                        continue
                
                existing_doc = await self.notion_repository.get_document(doc.id)
                if existing_doc:
                    has_changes = (
                        doc.title != existing_doc.title or
                        doc.last_edited_time > existing_doc.last_edited_time or
                        doc.properties != existing_doc.properties
                    )
                    
                    if has_changes:
                        logger.info(f"Update detected for document: {title}")
                        edited_by = await self._get_user_safely(doc.last_edited_by.id)
                        await self.notion_repository.save_document(doc)
                        
                        self._last_update_times[doc.id] = current_time
                        
                        notifications.append(NotificationMessage(
                            title=MESSAGE_TEMPLATES["update"].format(doc.title),
                            content=self._format_update_message(doc, edited_by),
                            timestamp=doc.last_edited_time,
                            channels=self.notification_channels
                        ))
            
            logger.info(f"Created {len(notifications)} update notifications")
            return notifications
        except Exception as e:
            logger.error(f"Error handling updates: {e}")
            return []

    async def _process_document_update(
        self, 
        doc: NotionDocument, 
        current_time: datetime
    ) -> Optional[NotificationMessage]:
        """Process a single document update"""
        try:
            if doc.id in self._last_update_times:
                last_update = self._last_update_times[doc.id]
                if (current_time - last_update).total_seconds() < 900:
                    return None

            self._last_update_times[doc.id] = current_time
            last_known_update = await self.notion_repository.get_last_update_time(doc.id)

            if not last_known_update or doc.last_edited_time > last_known_update:
                title = doc.title[0]['plain_text'] if isinstance(doc.title, list) else doc.title
                doc.title = title
                
                logger.info(f"Saving updated document to database: {title}")
                await self.notion_repository.save_document(doc)
                
                edited_by = await self._get_user_safely(doc.last_edited_by.id)
                
                return NotificationMessage(
                    title=MESSAGE_TEMPLATES["update"].format(doc.title),
                    content=self._format_update_message(doc, edited_by),
                    timestamp=doc.last_edited_time,
                    channels=self.notification_channels
                )
        except Exception as e:
            logger.error(f"Error processing document update: {e}", exc_info=True)
            return None
        return None

    def _format_update_message(self, doc: NotionDocument, edited_by: str) -> str:
        """Format update message for Discord"""
        title = MESSAGE_TEMPLATES["update"].format(doc.title)
        return f"{title}\n**Edited By:** {edited_by}\n**Time:** <t:{int(doc.last_edited_time.timestamp())}:F>\n**Link:** {doc.url}"

    def _format_creation_message(self, doc: NotionDocument, created_by: str) -> str:
        """Format creation message for Discord"""
        title = MESSAGE_TEMPLATES["creation"].format(doc.title)
        return f"{title}\n**Created By:** {created_by}\n**Time:** <t:{int(doc.created_time.timestamp())}:F>\n**Link:** {doc.url}"

    async def handle_aggregate_updates(self, start_time: datetime) -> Optional[NotificationMessage]:
        """Handle weekly aggregate updates"""
        try:
            updated_docs = await self.notion_repository.get_documents_updated_since(start_time)
            if not updated_docs:
                return None

            content = "Weekly Update Summary:\n\n"
            for doc in updated_docs:
                edited_by = await self._get_user_safely(doc.last_edited_by.id)
                content += f"• {doc.title} - Updated by {edited_by}\n"

            return NotificationMessage(
                title=MESSAGE_TEMPLATES["weekly_summary"],
                content=content,
                timestamp=datetime.now(),
                channels=self.notification_channels
            )
        except Exception as e:
            logger.error(f"Error handling aggregate updates: {e}")
            return None

    async def _send_notification(self, notification: NotificationMessage):
        """Send a notification through Discord"""
        try:
            for channel_id in notification.channels:
                await self.discord_service.send_message(
                    channel_id=channel_id,
                    title=notification.title,
                    content=notification.content
                )
        except Exception as e:
            logger.error(f"Error sending notification: {e}") 