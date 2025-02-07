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
from src.utils.notion_utils import extract_title

def extract_clean_title(page: dict) -> str:
    """Extract clean title without IDs from page data"""
    # Try properties first
    if 'properties' in page:
        for prop_name in ['Page', 'Name', 'Title']:
            if prop_name in page['properties']:
                title_prop = page['properties'][prop_name].get('title', [])
                if title_prop and isinstance(title_prop, list):
                    plain_text = title_prop[0].get('plain_text', '').strip()
                    # Remove any trailing alphanumeric strings that look like IDs
                    if plain_text:
                        parts = plain_text.split()
                        if len(parts[-1]) == 32 and parts[-1].isalnum():
                            plain_text = ' '.join(parts[:-1])
                        return plain_text

    # Try root title
    if 'title' in page:
        title_array = page['title']
        if isinstance(title_array, list) and title_array:
            title = title_array[0].get('plain_text', '').strip()
            if title:
                return title

    # Last resort
    return "Untitled Document"

async def migrate_data(data=None, session_factory=None):
    """Migrate data from JSON to database"""
    if session_factory is None:
        session_factory = create_session()
    
    if data is None:
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'db.json')
        try:
            with open(json_path, 'r') as f:
                raw_data = json.load(f)
                if isinstance(raw_data, dict) and "_default" in raw_data:
                    data = list(raw_data["_default"].values())
                else:
                    data = raw_data
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in db.json")
    
    async with session_factory() as session:
        async with session.begin():
            # First, collect and create all users
            users = set()
            for page in data:
                if page.get('object') != 'page':
                    continue
                
                created_by = page.get('created_by', {})
                last_edited_by = page.get('last_edited_by', {})
                
                if created_by and 'id' in created_by:
                    users.add((
                        created_by['id'],
                        created_by.get('name', 'Unknown'),
                        created_by.get('avatar_url', '')
                    ))
                if last_edited_by and 'id' in last_edited_by:
                    users.add((
                        last_edited_by['id'],
                        last_edited_by.get('name', 'Unknown'),
                        last_edited_by.get('avatar_url', '')
                    ))
            
            # Create users
            for user_id, name, avatar_url in users:
                user = NotionUserModel(
                    id=user_id,
                    name=name,
                    avatar_url=avatar_url
                )
                session.add(user)
            
            # Track documents and their versions
            document_versions = {}  # doc_id -> list of page versions

            # First pass - collect all versions
            for page in data:
                if page.get('object') != 'page':
                    continue
                
                if not all(key in page for key in ['id', 'created_time', 'last_edited_time']):
                    continue
                
                doc_id = page['id']
                if doc_id not in document_versions:
                    document_versions[doc_id] = []
                document_versions[doc_id].append(page)

            # Now process documents and their versions
            for doc_id, versions in document_versions.items():
                # Sort versions by last_edited_time
                versions.sort(key=lambda x: datetime.fromisoformat(x['last_edited_time'].replace('Z', '+00:00')))
                
                # Use latest version for the main document
                latest_version = versions[-1]
                title = extract_clean_title(latest_version)
                
                # Create the main document
                doc = NotionDocumentModel(
                    id=doc_id,
                    object=latest_version.get('object', 'page'),
                    created_time=datetime.fromisoformat(versions[0]['created_time'].replace('Z', '+00:00')),
                    last_edited_time=datetime.fromisoformat(latest_version['last_edited_time'].replace('Z', '+00:00')),
                    created_by_id=latest_version.get('created_by', {}).get('id'),
                    last_edited_by_id=latest_version.get('last_edited_by', {}).get('id'),
                    title=title,
                    url=latest_version.get('url', ''),
                    archived=latest_version.get('archived', False),
                    properties=latest_version.get('properties', {})
                )
                session.add(doc)
                
                # Create all versions
                for version in versions:
                    version_title = extract_clean_title(version)
                    version_record = NotionDocumentVersionModel(
                        document_id=doc_id,
                        object=version.get('object', 'page'),
                        created_time=datetime.fromisoformat(version['created_time'].replace('Z', '+00:00')),
                        last_edited_time=datetime.fromisoformat(version['last_edited_time'].replace('Z', '+00:00')),
                        created_by_id=version.get('created_by', {}).get('id'),
                        last_edited_by_id=version.get('last_edited_by', {}).get('id'),
                        title=version_title,
                        url=version.get('url', ''),
                        archived=version.get('archived', False),
                        properties=version.get('properties', {})
                    )
                    session.add(version_record)
                
                print(f"Processed document with {len(versions)} versions: {title}")

if __name__ == "__main__":
    asyncio.run(migrate_data())