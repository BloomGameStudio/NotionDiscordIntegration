import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SAWarning
from sqlalchemy.sql import select
from src.infrastructure.database.models import Base, NotionDocumentModel
from src.domain.notion.entities import NotionDocument, NotionUser
import warnings

@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)

def test_basic_crud(db_session):
    # Create
    doc = NotionDocumentModel(
        id="test-id",
        object="page",
        created_time=datetime.now(timezone.utc),
        last_edited_time=datetime.now(timezone.utc),
        created_by_id="user1",
        last_edited_by_id="user2",
        title="Test Document",
        url="https://notion.so/test",
        archived=False,
        properties={}
    )
    
    db_session.add(doc)
    db_session.commit()
    
    # Read
    result = db_session.get(NotionDocumentModel, "test-id")
    assert result is not None
    assert result.title == "Test Document"
    
    # Update
    result.title = "Updated Title"
    db_session.commit()
    updated = db_session.get(NotionDocumentModel, "test-id")
    assert updated.title == "Updated Title"
    
    # Delete
    db_session.delete(result)
    db_session.commit()
    deleted = db_session.get(NotionDocumentModel, "test-id")
    assert deleted is None

@pytest.mark.asyncio
async def test_entity_conversion():
    # Test to_entity and from_entity methods
    doc_model = NotionDocumentModel(
        id="test-id",
        object="page",
        created_time=datetime.now(timezone.utc),
        last_edited_time=datetime.now(timezone.utc),
        created_by_id="user1",
        last_edited_by_id="user2",
        title="Test Document",
        url="https://notion.so/test",
        archived=False,
        properties={"test": "value"}
    )
    
    # Test model -> entity conversion
    entity = doc_model.to_entity()
    assert isinstance(entity, NotionDocument)
    assert entity.created_by.id == doc_model.created_by_id
    
    # Test entity -> model conversion
    new_model = NotionDocumentModel.from_entity(entity)
    assert new_model.id == doc_model.id
    assert new_model.properties == doc_model.properties

@pytest.mark.asyncio
async def test_duplicate_error(db_session):
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=SAWarning)
        
        doc1 = NotionDocumentModel(
            id="duplicate-id",
            object="page",
            created_time=datetime.now(timezone.utc),
            last_edited_time=datetime.now(timezone.utc),
            created_by_id="user1",
            last_edited_by_id="user2",
            title="Original Document"
        )
        
        doc2 = NotionDocumentModel(
            id="duplicate-id",
            object="page",
            created_time=datetime.now(timezone.utc),
            last_edited_time=datetime.now(timezone.utc),
            created_by_id="user1",
            last_edited_by_id="user2",
            title="Duplicate Document"
        )
        
        db_session.add(doc1)
        db_session.commit()
        
        db_session.add(doc2)
        with pytest.raises(IntegrityError):
            db_session.commit()

@pytest.mark.asyncio
async def test_batch_operations(db_session):
    docs = [
        NotionDocumentModel(
            id=f"test-id-{i}",
            object="page",
            created_time=datetime.now(timezone.utc),
            last_edited_time=datetime.now(timezone.utc),
            created_by_id="user1",
            last_edited_by_id="user2",
            title=f"Test Document {i}"
        ) for i in range(5)
    ]
    
    db_session.add_all(docs)
    db_session.commit()
    
    result = db_session.execute(select(NotionDocumentModel))
    all_docs = result.scalars().all()
    assert len(all_docs) == 5 