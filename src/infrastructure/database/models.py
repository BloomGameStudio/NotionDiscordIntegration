from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Integer,
    Table,
    func,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from src.domain.notion.entities import NotionDocument, NotionUser
import uuid

Base = declarative_base()

# Association tables for many-to-many relationships
document_creators = Table(
    "notion_document_creators",
    Base.metadata,
    Column("document_id", String(255), ForeignKey("notion_documents.id")),
    Column("user_id", String(255), ForeignKey("notion_users.id")),
)

document_assignees = Table(
    "notion_document_assignees",
    Base.metadata,
    Column("document_id", String(255), ForeignKey("notion_documents.id")),
    Column("user_id", String(255), ForeignKey("notion_users.id")),
)


class NotionUserModel(Base):
    __tablename__ = "notion_users"

    id = Column(String(255), primary_key=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    type = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)


class NotionDocumentModel(Base):
    __tablename__ = "notion_documents"

    id = Column(String(255), primary_key=True)
    object = Column(String(50), nullable=False)
    created_time = Column(DateTime(timezone=True), nullable=False)
    last_edited_time = Column(DateTime(timezone=True), nullable=False)
    title = Column(JSON)
    url = Column(String)
    archived = Column(Boolean, default=False)
    properties = Column(JSON)
    created_by_id = Column(String(255), ForeignKey("notion_users.id"))
    last_edited_by_id = Column(String(255), ForeignKey("notion_users.id"))

    # Direct relationships to users
    created_by = relationship("NotionUserModel", foreign_keys=[created_by_id])
    last_edited_by = relationship("NotionUserModel", foreign_keys=[last_edited_by_id])

    # Add the relationship to versions
    versions = relationship("NotionDocumentVersionModel", back_populates="document")

    def to_entity(self) -> NotionDocument:
        return NotionDocument(
            id=self.id,
            object=self.object,
            created_time=self.created_time,
            last_edited_time=self.last_edited_time,
            created_by=NotionUser(id=self.created_by_id),
            last_edited_by=NotionUser(id=self.last_edited_by_id),
            title=self.title,
            url=self.url,
            archived=self.archived,
            properties=self.properties,
        )

    @classmethod
    def from_entity(cls, entity: NotionDocument) -> "NotionDocumentModel":
        return cls(
            id=entity.id,
            object=entity.object,
            created_time=entity.created_time,
            last_edited_time=entity.last_edited_time,
            created_by_id=entity.created_by.id if entity.created_by else None,
            last_edited_by_id=(
                entity.last_edited_by.id if entity.last_edited_by else None
            ),
            title=entity.title,
            url=entity.url,
            archived=entity.archived,
            properties=entity.properties,
        )

    def get_last_update_time(self) -> datetime:
        return self.last_edited_time


class NotionDocumentVersionModel(Base):
    __tablename__ = "notion_document_versions"

    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(255), ForeignKey("notion_documents.id"))
    object = Column(String(50), nullable=False)
    created_time = Column(DateTime(timezone=True), nullable=False)
    last_edited_time = Column(DateTime(timezone=True), nullable=False)
    title = Column(String)
    url = Column(String)
    archived = Column(Boolean, default=False)
    properties = Column(JSON)
    created_by_id = Column(String(255), ForeignKey("notion_users.id"))
    last_edited_by_id = Column(String(255), ForeignKey("notion_users.id"))

    # Relationships
    document = relationship("NotionDocumentModel", back_populates="versions")
    created_by = relationship("NotionUserModel", foreign_keys=[created_by_id])
    last_edited_by = relationship("NotionUserModel", foreign_keys=[last_edited_by_id])


class NotionStateModel(Base):
    __tablename__ = "notion_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_sync_time = Column(DateTime(timezone=True), nullable=False, default=func.now())
    cursor = Column(String, nullable=True)
    sync_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
