from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from src.infrastructure.database.models import (
    NotionDocumentModel,
    NotionUserModel,
    NotionDocumentVersionModel,
)
from src.domain.notion.entities import NotionDocument, NotionUser


class NotionRepository(ABC):
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[NotionDocument]:
        pass

    @abstractmethod
    def save_document(self, document: NotionDocument) -> None:
        pass

    @abstractmethod
    def get_documents_updated_since(self, timestamp: datetime) -> List[NotionDocument]:
        pass

    @abstractmethod
    def get_last_update_time(self, document_id: str) -> Optional[datetime]:
        pass


class SQLNotionRepository(NotionRepository):
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def get_document(self, document_id: str) -> Optional[NotionDocument]:
        with self.session_factory() as session:
            result = session.get(NotionDocumentModel, document_id)
            if not result:
                return None

            return NotionDocument(
                id=result.id,
                object=result.object,
                created_time=result.created_time,
                last_edited_time=result.last_edited_time,
                created_by=NotionUser(id=result.created_by_id)
                if result.created_by_id
                else None,
                last_edited_by=NotionUser(id=result.last_edited_by_id)
                if result.last_edited_by_id
                else None,
                title=result.title,
                url=result.url,
                archived=result.archived,
                properties=result.properties,
            )

    def save_document(self, document: NotionDocument) -> None:
        """Save document to database"""
        with self.session_factory() as session:
            doc_model = NotionDocumentModel(
                id=document.id,
                object=document.object,
                created_time=document.created_time,
                last_edited_time=document.last_edited_time,
                created_by_id=document.created_by.id if document.created_by else None,
                last_edited_by_id=document.last_edited_by.id
                if document.last_edited_by
                else None,
                title=document.title,
                url=document.url,
                archived=document.archived,
                properties=document.properties,
            )
            session.merge(doc_model)
            session.commit()

    def get_documents_updated_since(self, timestamp: datetime) -> List[NotionDocument]:
        stmt = select(NotionDocumentModel).where(
            NotionDocumentModel.last_edited_time >= timestamp
        )
        with self.session_factory() as session:
            result = session.execute(stmt)
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
                    properties=doc.properties,
                )
                for doc in documents
            ]

    def _ensure_user_exists(self, session: Session, user: NotionUser) -> None:
        if not user:
            return

        existing = session.get(NotionUserModel, user.id)
        if not existing:
            user_model = NotionUserModel(
                id=user.id, name=user.name or "Unknown User", avatar_url=user.avatar_url
            )
            session.add(user_model)

    async def save_user(self, user_data: dict):
        with self.session_factory() as session:
            existing = session.get(NotionUserModel, user_data["id"])

            if existing:
                existing.name = user_data.get("name", "Unknown User")
                existing.email = user_data.get("email")
                existing.type = user_data.get("type", "person")
                existing.avatar_url = user_data.get("avatar_url")
            else:
                user = NotionUserModel(
                    id=user_data["id"],
                    name=user_data.get("name", "Unknown User"),
                    email=user_data.get("email"),
                    type=user_data.get("type", "person"),
                    avatar_url=user_data.get("avatar_url"),
                )
                session.add(user)

            session.commit()

    def get_last_update_time(self, document_id: str) -> Optional[datetime]:
        with self.session_factory() as session:
            result = session.get(NotionDocumentModel, document_id)
            if not result:
                return None
            return result.last_edited_time
