from typing import List, Optional, Any
from datetime import datetime
from notion_client import AsyncClient
from src.domain.notion.entities import NotionDocument
from src.utils.logging import logger
import asyncio

class NotionClient:
    def __init__(self, auth_token: str, database_id: str):
        self.client = AsyncClient(auth=auth_token)
        self.database_id = database_id
        self._user_cache = {}

    async def retry_async(
        self, 
        coro: Any, 
        *args, 
        retries: int = 3, 
        delay: int = 1, 
        backoff_factor: int = 2, 
        **kwargs
    ) -> Any:
        """Generic retry decorator for async operations"""
        attempt = 0
        while attempt < retries:
            try:
                return await coro(*args, **kwargs)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with error: {e}")
                attempt += 1
                if attempt >= retries:
                    logger.error(f"All {retries} attempts failed. No more retries.")
                    raise
                sleep_time = delay * (backoff_factor ** (attempt - 1))
                logger.info(f"Retrying in {sleep_time} seconds...")
                await asyncio.sleep(sleep_time)

    async def get_document(self, document_id: str) -> Optional[NotionDocument]:
        """Fetch a single document from Notion API"""
        try:
            response = await self.retry_async(
                self.client.pages.retrieve,
                page_id=document_id
            )
            return NotionDocument.from_api_response(response)
        except Exception as e:
            logger.error(f"Error fetching document {document_id}: {e}")
            return None

    async def get_all_documents(self) -> List[NotionDocument]:
        """Fetch all documents from the database"""
        try:
            documents = []
            has_more = True
            start_cursor = None

            while has_more:
                response = await self.retry_async(
                    self.client.databases.query,
                    database_id=self.database_id,
                    start_cursor=start_cursor
                )
                
                documents.extend([
                    NotionDocument.from_api_response(page)
                    for page in response["results"]
                ])
                
                has_more = response["has_more"]
                start_cursor = response["next_cursor"]

            return documents
        except Exception as e:
            logger.error(f"Error fetching all documents: {e}")
            return []

    async def get_recent_documents(self, limit: int = 100) -> List[NotionDocument]:
        """Fetch recent documents from the database"""
        try:
            response = await self.retry_async(
                self.client.databases.query,
                database_id=self.database_id,
                page_size=limit,
                sorts=[{
                    "timestamp": "created_time",
                    "direction": "descending"
                }]
            )
            
            return [
                NotionDocument.from_api_response(page)
                for page in response["results"]
            ]
        except Exception as e:
            logger.error(f"Error fetching recent documents: {e}")
            return []

    async def get_updated_documents(self) -> List[NotionDocument]:
        """Fetch recently updated documents"""
        try:
            logger.debug("Querying Notion database for updates...")
            documents = []
            has_more = True
            start_cursor = None

            while has_more:
                response = await self.retry_async(
                    self.client.databases.query,
                    database_id=self.database_id,
                    start_cursor=start_cursor,
                    sorts=[{
                        "timestamp": "last_edited_time",
                        "direction": "descending"
                    }]
                )
                
                documents.extend([
                    NotionDocument.from_api_response(page)
                    for page in response["results"]
                ])
                
                has_more = response["has_more"]
                start_cursor = response["next_cursor"]

            logger.debug(f"Received total of {len(documents)} results from Notion")
            return documents
        except Exception as e:
            logger.error(f"Error fetching updated documents: {e}")
            return []

    async def get_user(self, user_id: str) -> dict:
        """Get user details for a user ID, with caching"""
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        
        try:
            user = await self.retry_async(
                self.client.users.retrieve,
                user_id=user_id
            )
            self._user_cache[user_id] = user.get('name', 'Unknown User')
            return self._user_cache[user_id]
        except Exception as e:
            logger.debug(f"Could not fetch user {user_id}, using ID as name: {e}")
            self._user_cache[user_id] = user_id[:8]
            return self._user_cache[user_id] 