from datetime import datetime, timedelta
import asyncio
from typing import List, Optional
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
        notification_channels: List[int]
    ):
        self.notion_client = notion_client
        self.notion_repository = notion_repository
        self.notification_channels = notification_channels
        self._last_update_times = {}

    async def sync_db(self) -> None:
        """Sync the database with Notion"""
        try:
            # Get all documents from Notion
            documents = await self.notion_client.get_all_documents()
            
            # Save/update documents
            for doc in documents:
                await self.notion_repository.save_document(doc)
            
        except Exception as e:
            logger.error(f"Error syncing database: {e}")
            raise

    async def handle_creations(self) -> List[NotificationMessage]:
        """Handle newly created documents"""
        try:
            latest_docs = await self.notion_client.get_recent_documents()
            notifications = []

            for doc in latest_docs:
                existing_doc = await self.notion_repository.get_document(doc.id)
                if not existing_doc:
                    await self.notion_repository.save_document(doc)
                    edited_by = await self.notion_client.get_user(doc.created_by.id)
                    
                    notifications.append(NotificationMessage(
                        title=f"🎉 **New Entry Created: {doc.title}**",
                        content=self._format_creation_message(doc, edited_by),
                        timestamp=doc.created_time,
                        channels=self.notification_channels
                    ))

            return notifications
        except Exception as e:
            logger.error(f"Error handling creations: {e}")
            return []

    async def handle_updates(self) -> List[NotificationMessage]:
        """Handle document updates"""
        try:
            current_time = datetime.now()
            logger.debug("Fetching updated documents from Notion...")
            documents = await self.notion_client.get_updated_documents()
            logger.debug(f"Found {len(documents)} documents to process")
            notifications = []

            for doc in documents:
                logger.debug(f"Processing document: {doc.id} - {doc.title}")
                notification = await self._process_document_update(doc, current_time)
                if notification:
                    logger.debug(f"Created notification for document: {doc.id}")
                    notifications.append(notification)
                else:
                    logger.debug(f"No notification created for document: {doc.id} (might be in cooldown)")

            return notifications
        except Exception as e:
            logger.error(f"Error handling updates: {e}", exc_info=True)
            return []

    async def _process_document_update(
        self, 
        doc: NotionDocument, 
        current_time: datetime
    ) -> Optional[NotificationMessage]:
        """Process a single document update"""
        if doc.id in self._last_update_times:
            last_update = self._last_update_times[doc.id]
            if (current_time - last_update).total_seconds() < 900:  # 15 minutes
                return None

        self._last_update_times[doc.id] = current_time
        last_known_update = await self.notion_repository.get_last_update_time(doc.id)

        if not last_known_update or doc.last_edited_time > last_known_update:
            await self.notion_repository.save_document(doc)
            edited_by = await self.notion_client.get_user(doc.last_edited_by.id)
            
            return NotificationMessage(
                title=f"📡**__{doc.title} Update__**📡",
                content=self._format_update_message(doc, edited_by),
                timestamp=doc.last_edited_time,
                channels=self.notification_channels
            )
        return None

    def _format_update_message(self, doc: NotionDocument, edited_by: str) -> str:
        """Format update message for Discord"""
        title = MESSAGE_TEMPLATES["update"].format(title=doc.title)
        return f"{title}\n**Edited By:** {edited_by}\n**Time:** <t:{int(doc.last_edited_time.timestamp())}:F>\n**Link:** {doc.url}"

    def _format_creation_message(self, doc: NotionDocument, created_by: str) -> str:
        """Format creation message for Discord"""
        title = MESSAGE_TEMPLATES["creation"].format(title=doc.title)
        return f"{title}\n**Created By:** {created_by}\n**Time:** <t:{int(doc.created_time.timestamp())}:F>\n**Link:** {doc.url}"

    async def handle_aggregate_updates(self, start_time: datetime) -> Optional[NotificationMessage]:
        """Handle weekly aggregate updates"""
        try:
            updated_docs = await self.notion_repository.get_documents_updated_since(start_time)
            if not updated_docs:
                return None

            content = "Weekly Update Summary:\n\n"
            for doc in updated_docs:
                edited_by = await self.notion_client.get_user(doc.last_edited_by.id)
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