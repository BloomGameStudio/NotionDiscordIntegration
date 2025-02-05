#!/usr/bin/env python3
import asyncio
import json
import os
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import uuid  # Add this import at the top

from src.infrastructure.database.models import (
    Base, 
    NotionDocumentModel, 
    NotionUserModel, 
    NotionStateModel,
    NotionDocumentVersionModel
)
from src.infrastructure.config.database import create_session

async def migrate_data(data=None, session_factory=None):
    """Migrate data to the database"""
    if session_factory is None:
        session_factory = create_session()
    
    if data is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        json_path = os.path.join(project_root, 'db.json')
        with open(json_path, 'r') as f:
            raw_data = json.load(f)
            if "_default" in raw_data:
                data = [doc for doc in raw_data["_default"].values() 
                       if doc.get("object") == "page"]
            else:
                data = []
    
    engine = session_factory.kw['bind']
    async with engine.begin() as conn:
        # Drop all tables first
        await conn.run_sync(Base.metadata.drop_all)
        # Then create them again with the new schema
        await conn.run_sync(Base.metadata.create_all)
    
    async with session_factory() as session:
        async with session.begin():
            # First, create users
            users = set()
            for page in data:
                for user_field in ['created_by', 'last_edited_by']:
                    if user_data := page.get(user_field):
                        user_id = user_data.get('id')
                        if user_id and user_id not in users:
                            users.add(user_id)  # Add to set to prevent duplicates
                            user = NotionUserModel(
                                id=user_id,
                                name=user_data.get('name', ''),
                                type='person'
                            )
                            session.add(user)
            
            await session.flush()  # Ensure users are created before documents
            
            # Then process documents
            processed_docs = set()
            for page in data:
                if not all(key in page for key in ['id', 'created_time', 'last_edited_time']):
                    raise ValueError("Missing required fields in document data")
                
                doc_id = page['id']
                title = page.get('title', '')
                
                # Extract title - first try direct title, then properties
                if not title and 'properties' in page and 'Page' in page['properties']:
                    title_parts = page['properties']['Page'].get('title', [])
                    if title_parts:
                        title = title_parts[0].get('plain_text', '')
                
                if doc_id not in processed_docs:
                    doc = NotionDocumentModel(
                        id=doc_id,
                        object=page.get('object', 'page'),
                        created_time=datetime.fromisoformat(page['created_time'].replace('Z', '+00:00')),
                        last_edited_time=datetime.fromisoformat(page['last_edited_time'].replace('Z', '+00:00')),
                        created_by_id=page.get('created_by', {}).get('id'),
                        last_edited_by_id=page.get('last_edited_by', {}).get('id'),
                        title=title,
                        url=page.get('url', ''),
                        archived=page.get('archived', False),
                        properties=page.get('properties', {})
                    )
                    session.add(doc)
                    processed_docs.add(doc_id)
                
                version = NotionDocumentVersionModel(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    object=page.get('object', 'page'),
                    created_time=datetime.fromisoformat(page['created_time'].replace('Z', '+00:00')),
                    last_edited_time=datetime.fromisoformat(page['last_edited_time'].replace('Z', '+00:00')),
                    created_by_id=page.get('created_by', {}).get('id'),
                    last_edited_by_id=page.get('last_edited_by', {}).get('id'),
                    title=title,
                    url=page.get('url', ''),
                    archived=page.get('archived', False),
                    properties=page.get('properties', {})
                )
                session.add(version)
                print(f"Processed document and version: {title or doc_id}")
            
            # Final commit
            await session.commit()

if __name__ == "__main__":
    asyncio.run(migrate_data())