import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from datetime import datetime, timezone
from src.domain.notion.entities import NotionDocument, NotionUser
from src.application.notion.notion_service import NotionService
from src.domain.notion.repositories import SQLNotionRepository
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_handle_updates():
    # Mock data
    test_doc = NotionDocument(
        id="test-id",
        object="page",
        created_time=datetime.now(timezone.utc),
        last_edited_time=datetime.now(timezone.utc),
        created_by=NotionUser(id="user1"),
        last_edited_by=NotionUser(id="user2"),
        title="Test Document",
        url="https://notion.so/test",
        archived=False,
        properties={}
    )
    
    async def mock_get_updated_documents(self):
        return [test_doc]
    
    async def mock_get_user(self, user_id: str):
        return "Test User"
    
    notion_client = type('MockNotionClient', (), {
        'get_updated_documents': mock_get_updated_documents,
        'get_user': mock_get_user
    })()
    
    # Use async mocks for repository
    notion_repository = type('MockRepository', (), {
        'get_document': AsyncMock(return_value=None),
        'save_document': AsyncMock()
    })()
    
    service = NotionService(
        notion_client=notion_client,
        notion_repository=notion_repository,
        notification_channels=[123456789]
    )
    
    notifications = await service.handle_updates()
    assert len(notifications) == 1
    assert "Test Document" in notifications[0].content

@pytest.mark.asyncio
async def test_handle_updates_error():
    async def mock_get_updates():
        raise Exception("API Error")
    
    notion_client = type('MockNotionClient', (), {'get_updates': mock_get_updates})()
    service = NotionService(
        notion_client=notion_client,
        notion_repository=None,
        notification_channels=[123456789]
    )
    
    notifications = await service.handle_updates()
    assert len(notifications) == 0

@pytest.mark.asyncio
async def test_handle_empty_updates():
    async def mock_get_updates():
        return []
    
    notion_client = type('MockNotionClient', (), {'get_updates': mock_get_updates})()
    service = NotionService(
        notion_client=notion_client,
        notion_repository=None,
        notification_channels=[123456789]
    )
    
    notifications = await service.handle_updates()
    assert len(notifications) == 0 

@pytest.mark.asyncio
async def test_sync_db():
    async def mock_get_all_documents(self):
        return [NotionDocument(
            id="test-id",
            object="page",
            created_time=datetime.now(timezone.utc),
            last_edited_time=datetime.now(timezone.utc),
            created_by=NotionUser(id="user1"),
            last_edited_by=NotionUser(id="user2"),
            title="Test Doc"
        )]
    
    notion_client = type('MockNotionClient', (), {'get_all_documents': mock_get_all_documents})()
    notion_repository = type('MockRepository', (), {'save_document': AsyncMock()})()
    
    service = NotionService(notion_client, notion_repository, [123])
    await service.sync_db()

@pytest.mark.asyncio
async def test_handle_creations():
    async def mock_get_recent_documents():
        return [NotionDocument(
            id="test-id",
            object="page",
            created_time=datetime.now(timezone.utc),
            last_edited_time=datetime.now(timezone.utc),
            created_by=NotionUser(id="user1"),
            last_edited_by=NotionUser(id="user2"),
            title="Test Doc"
        )]
    
    notion_client = type('MockNotionClient', (), {'get_recent_documents': mock_get_recent_documents})()
    # Use async mocks for repository
    notion_repository = type('MockRepository', (), {
        'get_document': AsyncMock(return_value=None),
        'save_document': AsyncMock()
    })()
    
    service = NotionService(notion_client, notion_repository, [123])
    notifications = await service.handle_creations()
    assert len(notifications) == 1

@pytest.mark.asyncio
async def test_handle_aggregate_updates():
    test_docs = [NotionDocument(
        id="doc1",
        object="page",
        created_time=datetime.now(timezone.utc),
        last_edited_time=datetime.now(timezone.utc),
        created_by=NotionUser(id="user1"),
        last_edited_by=NotionUser(id="user2"),
        title="Doc 1",
        url="https://notion.so/test"
    )]
    
    async def mock_get_docs_since(self, time):
        return test_docs
    
    notion_client = type('MockNotionClient', (), {
        'get_user': AsyncMock(return_value="Test User")
    })()
    notion_repository = type('MockRepository', (), {
        'get_documents_updated_since': mock_get_docs_since,
        'save_document': AsyncMock()
    })()
    
    service = NotionService(notion_client, notion_repository, [123])
    result = await service.handle_aggregate_updates(datetime.now(timezone.utc))
    assert result is not None
    assert len(result.content) > 0 