import os
import json
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.infrastructure.database.models import Base, NotionDocumentModel, NotionDocumentVersionModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from src.scripts.migrate import migrate_data

@pytest.mark.asyncio
async def test_migration():
    test_data = [{
        "id": "test-id",
        "object": "page",
        "created_time": "2024-01-01T00:00:00Z",
        "last_edited_time": "2024-01-01T00:00:00Z",
        "created_by": {"id": "user1"},
        "last_edited_by": {"id": "user2"},
        "title": "Test Document",
        "url": "https://notion.so/test",
        "archived": False,
        "properties": {}
    }]
    
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await migrate_data(test_data)

@pytest.mark.asyncio
async def test_migration_invalid_json():
    json_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'db.json')
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        with open(json_path, 'w') as f:
            f.write('invalid json')
        
        with pytest.raises(json.JSONDecodeError):
            await migrate_data(None, session_factory)
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)

@pytest.mark.asyncio
async def test_migration_missing_required_fields():
    test_data = [{"id": "test-id"}]  # Missing required fields
    with pytest.raises(ValueError):
        await migrate_data(test_data)

@pytest.mark.asyncio
async def test_migration_duplicate_documents():
    test_data = [
        {
            "id": "same-id",
            "object": "page",
            "created_time": "2024-01-01T00:00:00Z",
            "last_edited_time": "2024-01-01T00:00:00Z",
            "created_by": {"id": "user1"},
            "last_edited_by": {"id": "user2"},
            "title": "Doc 1",
            "url": "https://notion.so/test",
            "archived": False,
            "properties": {}
        },
        {
            "id": "same-id",
            "object": "page",
            "created_time": "2024-01-01T00:00:00Z",
            "last_edited_time": "2024-01-01T00:00:00Z",
            "created_by": {"id": "user1"},
            "last_edited_by": {"id": "user2"},
            "title": "Doc 2",
            "url": "https://notion.so/test",
            "archived": False,
            "properties": {}
        }
    ]
    
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await migrate_data(test_data, session_factory)
    
    async with session_factory() as session:
        result = await session.execute(select(NotionDocumentModel))
        documents = result.scalars().all()
        assert len(documents) == 1
        assert documents[0].id == "same-id"
        assert documents[0].title == "Doc 1"  # First document should be kept
        
        # Check versions
        result = await session.execute(select(NotionDocumentVersionModel))
        versions = result.scalars().all()
        assert len(versions) == 2

@pytest.mark.asyncio
async def test_migration_missing_title():
    test_data = [{
        "id": "test-id-no-title",
        "object": "page",
        "created_time": "2024-01-01T00:00:00Z",
        "last_edited_time": "2024-01-01T00:00:00Z",
        "created_by": {"id": "user1"},
        "last_edited_by": {"id": "user2"},
        "url": "https://notion.so/test-page",
        "archived": False,
        "properties": {}
    }]
    
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await migrate_data(test_data, session_factory)
    
    async with session_factory() as session:
        result = await session.execute(select(NotionDocumentModel))
        document = result.scalar_one()
        assert document.title is not None
        assert document.title.startswith("Untitled Page (")