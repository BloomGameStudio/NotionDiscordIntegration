from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infrastructure.database.models import NotionDocumentModel, NotionUserModel
from src.domain.notion.entities import NotionDocument, NotionUser
import logging

logger = logging.getLogger(__name__)

class NotionRepository(ABC):
    @abstractmethod
    async def get_all(self) -> List[NotionDocument]:
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[NotionDocument]:
        pass

    @abstractmethod
    async def save(self, document: NotionDocument) -> None:
        pass

class SQLNotionRepository(NotionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all(self) -> List[NotionDocument]:
        result = await self.session.execute(select(NotionDocumentModel))
        return [doc.to_entity() for doc in result.scalars().all()]
    
    async def get_by_id(self, id: str) -> Optional[NotionDocument]:
        result = await self.session.execute(
            select(NotionDocumentModel).where(NotionDocumentModel.id == id)
        )
        db_doc = result.scalar_one_or_none()
        return db_doc.to_entity() if db_doc else None
    
    async def save(self, document: NotionDocument) -> None:
        db_doc = NotionDocumentModel.from_entity(document)
        self.session.add(db_doc)
        await self.session.commit()
    
    async def get_documents_updated_since(self, timestamp: datetime) -> List[NotionDocument]:
        result = await self.session.execute(
            select(NotionDocumentModel)
            .where(NotionDocumentModel.last_edited_time > timestamp)
            .order_by(NotionDocumentModel.last_edited_time)
        )
        return [doc.to_entity() for doc in result.scalars().all()]
    
    async def get_last_update_time(self, document_id: str) -> Optional[datetime]:
        result = await self.session.execute(
            select(NotionDocumentModel.last_edited_time)
            .where(NotionDocumentModel.id == document_id)
            .order_by(NotionDocumentModel.last_edited_time.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def save_user(self, user_data: dict):
        """Save or update a user in the database"""
        # Check if user exists
        existing = await self.session.get(NotionUserModel, user_data['id'])
        
        if existing:
            # Update existing user
            existing.name = user_data.get('name', 'Unknown User')
            existing.email = user_data.get('email')
            existing.type = user_data.get('type', 'person')
            existing.avatar_url = user_data.get('avatar_url')
        else:
            # Create new user
            user = NotionUserModel(
                id=user_data['id'],
                name=user_data.get('name', 'Unknown User'),
                email=user_data.get('email'),
                type=user_data.get('type', 'person'),
                avatar_url=user_data.get('avatar_url')
            )
            self.session.add(user)
        
        await self.session.commit()

    async def save_document(self, document: NotionDocument):
        """Save or update a document in the database"""
        try:
            # First save users to satisfy foreign key constraints
            if document.created_by:
                await self.save_user({
                    'id': document.created_by.id,
                    'name': 'Unknown User',
                    'type': 'person'
                })
            if document.last_edited_by:
                await self.save_user({
                    'id': document.last_edited_by.id,
                    'name': 'Unknown User',
                    'type': 'person'
                })
            
            # Now check if document exists
            existing = await self.session.get(NotionDocumentModel, document.id)
            
            if existing:
                # Update existing document
                existing.object = document.object
                existing.created_time = document.created_time
                existing.last_edited_time = document.last_edited_time
                existing.title = document.title
                existing.url = document.url
                existing.archived = document.archived
                existing.properties = document.properties
                existing.created_by_id = document.created_by.id if document.created_by else None
                existing.last_edited_by_id = document.last_edited_by.id if document.last_edited_by else None
            else:
                # Create new document
                doc = NotionDocumentModel(
                    id=document.id,
                    object=document.object,
                    created_time=document.created_time,
                    last_edited_time=document.last_edited_time,
                    created_by_id=document.created_by.id if document.created_by else None,
                    last_edited_by_id=document.last_edited_by.id if document.last_edited_by else None,
                    title=document.title,
                    url=document.url,
                    archived=document.archived,
                    properties=document.properties
                )
                self.session.add(doc)

            await self.session.commit()
            
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            await self.session.rollback()
            raise

    async def get_document(self, document_id: str) -> Optional[NotionDocument]:
        """Get a document by ID"""
        result = await self.session.get(NotionDocumentModel, document_id)
        if not result:
            return None
        
        return NotionDocument(
            id=result.id,
            object=result.object,
            created_time=result.created_time,
            last_edited_time=result.last_edited_time,
            created_by=NotionUser(id=result.created_by_id),
            last_edited_by=NotionUser(id=result.last_edited_by_id),
            title=result.title,
            url=result.url,
            archived=result.archived,
            properties=result.properties
        )

    async def get_documents_updated_since(self, since: datetime) -> List[NotionDocument]:
        """Get all documents updated since a given time"""
        stmt = select(NotionDocumentModel).where(
            NotionDocumentModel.last_edited_time >= since
        )
        result = await self.session.execute(stmt)
        documents = result.scalars().all()
        
        return [
            NotionDocument(
                id=doc.id,
                object=doc.object,
                created_time=doc.created_time,
                last_edited_time=doc.last_edited_time,
                created_by=NotionUser(id=doc.created_by_id),
                last_edited_by=NotionUser(id=doc.last_edited_by_id),
                title=doc.title,
                url=doc.url,
                archived=doc.archived,
                properties=doc.properties
            )
            for doc in documents
        ] 
