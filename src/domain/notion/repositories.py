from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
import json
from src.domain.notion.entities import NotionDocument, NotionUser


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


class TableStorageNotionRepository(NotionRepository):
    def __init__(self, connection_string: str, table_name: str = "notionDocuments"):
        from azure.data.tables import TableServiceClient
        from azure.core.exceptions import ResourceNotFoundError

        self._resource_not_found_error = ResourceNotFoundError
        self.table_service = TableServiceClient.from_connection_string(connection_string)
        self.table_client = self.table_service.create_table_if_not_exists(table_name)

    def _to_iso(self, value: datetime) -> str:
        if value.tzinfo is None:
            return value.isoformat() + "+00:00"
        return value.isoformat()

    def _from_iso(self, value: Optional[str]) -> datetime:
        if not value:
            return datetime.utcnow()
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _to_entity(self, document: NotionDocument) -> dict:
        return {
            "PartitionKey": "doc",
            "RowKey": document.id,
            "object": document.object,
            "created_time": self._to_iso(document.created_time),
            "last_edited_time": self._to_iso(document.last_edited_time),
            "created_by_id": document.created_by.id if document.created_by else "",
            "last_edited_by_id": document.last_edited_by.id if document.last_edited_by else "",
            "title": document.title or "",
            "url": document.url or "",
            "archived": bool(document.archived),
            "properties": json.dumps(document.properties or {}),
        }

    def _from_entity(self, entity: dict) -> NotionDocument:
        return NotionDocument(
            id=entity["RowKey"],
            object=entity.get("object", "page"),
            created_time=self._from_iso(entity.get("created_time")),
            last_edited_time=self._from_iso(entity.get("last_edited_time")),
            created_by=NotionUser(id=entity.get("created_by_id", "")),
            last_edited_by=NotionUser(id=entity.get("last_edited_by_id", "")),
            title=entity.get("title", ""),
            url=entity.get("url") or None,
            archived=bool(entity.get("archived", False)),
            properties=json.loads(entity.get("properties", "{}")),
        )

    def get_all(self) -> List[NotionDocument]:
        entities = self.table_client.query_entities("PartitionKey eq 'doc'")
        return [self._from_entity(entity) for entity in entities]

    def get_by_id(self, id: str) -> Optional[NotionDocument]:
        return self.get_document(id)

    def save(self, document: NotionDocument) -> None:
        self.save_document(document)

    def save_document(self, document: NotionDocument):
        entity = self._to_entity(document)
        self.table_client.upsert_entity(entity=entity, mode="MERGE")

    def get_document(self, document_id: str) -> Optional[NotionDocument]:
        try:
            entity = self.table_client.get_entity(partition_key="doc", row_key=document_id)
            return self._from_entity(entity)
        except self._resource_not_found_error:
            return None

    def get_last_update_time(self, document_id: str) -> Optional[datetime]:
        document = self.get_document(document_id)
        if not document:
            return None
        return document.last_edited_time

    def get_documents_updated_since(self, since: datetime) -> List[NotionDocument]:
        # For this workload size, in-memory filtering is cheap and avoids Table query date formatting edge cases.
        documents = self.get_all()
        return [doc for doc in documents if doc.last_edited_time >= since]
