from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session
from src.infrastructure.database.models import (
    NotionDocumentModel,
    NotionUserModel,
    NotionDocumentVersionModel,
)
from src.domain.notion.entities import NotionDocument, NotionUser
import logging

logger = logging.getLogger(__name__)


class NotionRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[NotionDocument]:
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[NotionDocument]:
        pass

    @abstractmethod
    def save(self, document: NotionDocument) -> None:
        pass


class SQLNotionRepository(NotionRepository):
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def get_all(self) -> List[NotionDocument]:
        with self.session_factory() as session:
            result = session.execute(select(NotionDocumentModel))
            return [doc.to_entity() for doc in result.scalars().all()]

    def get_by_id(self, id: str) -> Optional[NotionDocument]:
        with self.session_factory() as session:
            result = session.execute(
                select(NotionDocumentModel).where(NotionDocumentModel.id == id)
            )
            db_doc = result.scalar_one_or_none()
            return db_doc.to_entity() if db_doc else None

    def save(self, document: NotionDocument) -> None:
        with self.session_factory() as session:
            db_doc = NotionDocumentModel.from_entity(document)
            session.add(db_doc)
            session.commit()

    def get_documents_updated_since(self, timestamp: datetime) -> List[NotionDocument]:
        with self.session_factory() as session:
            result = session.execute(
                select(NotionDocumentModel)
                .where(NotionDocumentModel.last_edited_time > timestamp)
                .order_by(NotionDocumentModel.last_edited_time)
            )
            return [doc.to_entity() for doc in result.scalars().all()]

    def get_last_update_time(self, document_id: str) -> Optional[datetime]:
        with self.session_factory() as session:
            result = session.execute(
                select(NotionDocumentModel.last_edited_time)
                .where(NotionDocumentModel.id == document_id)
                .order_by(NotionDocumentModel.last_edited_time.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    def save_user(self, user_data: dict):
        """Save or update a user in the database"""
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

    def _ensure_user_exists(self, session: Session, user: NotionUser) -> None:
        """Ensure user exists in database"""
        if not user:
            return

        existing = session.get(NotionUserModel, user.id)
        if not existing:
            user_model = NotionUserModel(
                id=user.id, name=user.name or "Unknown User", avatar_url=user.avatar_url
            )
            session.add(user_model)

    def save_document(self, document: NotionDocument):
        """Save or update a document in the database"""
        with self.session_factory() as session:
            with session.begin():
                self._ensure_user_exists(session, document.created_by)
                self._ensure_user_exists(session, document.last_edited_by)

                existing = session.get(NotionDocumentModel, document.id)

                version = NotionDocumentVersionModel(
                    document_id=document.id,
                    object=document.object,
                    created_time=document.created_time,
                    last_edited_time=document.last_edited_time,
                    created_by_id=(
                        document.created_by.id if document.created_by else None
                    ),
                    last_edited_by_id=(
                        document.last_edited_by.id if document.last_edited_by else None
                    ),
                    title=document.title,
                    url=document.url,
                    archived=document.archived,
                    properties=document.properties,
                )
                session.add(version)

                if existing:
                    existing.object = document.object
                    existing.created_time = document.created_time
                    existing.last_edited_time = document.last_edited_time
                    existing.title = document.title
                    existing.url = document.url
                    existing.archived = document.archived
                    existing.properties = document.properties
                    existing.created_by_id = (
                        document.created_by.id if document.created_by else None
                    )
                    existing.last_edited_by_id = (
                        document.last_edited_by.id if document.last_edited_by else None
                    )
                else:
                    doc = NotionDocumentModel(
                        id=document.id,
                        object=document.object,
                        created_time=document.created_time,
                        last_edited_time=document.last_edited_time,
                        created_by_id=(
                            document.created_by.id if document.created_by else None
                        ),
                        last_edited_by_id=(
                            document.last_edited_by.id
                            if document.last_edited_by
                            else None
                        ),
                        title=document.title,
                        url=document.url,
                        archived=document.archived,
                        properties=document.properties,
                    )
                    session.add(doc)

                session.commit()
                logger.info(
                    f"Successfully saved document and version: {document.title}"
                )

    def get_document(self, document_id: str) -> Optional[NotionDocument]:
        """Get a document by ID"""
        with self.session_factory() as session:
            result = session.get(NotionDocumentModel, document_id)
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
                properties=result.properties,
            )

    def get_documents_updated_since(self, since: datetime) -> List[NotionDocument]:
        """Get all documents updated since a given time"""
        stmt = select(NotionDocumentModel).where(
            NotionDocumentModel.last_edited_time >= since
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
