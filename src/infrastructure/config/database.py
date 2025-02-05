from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

def get_database_url():
    """Get database URL from environment variables"""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST', 'localhost')
        if not db_password:
            raise ValueError("Either DATABASE_URL or DB_PASSWORD environment variable is required")
        database_url = f'postgresql+asyncpg://notion_bot:{db_password}@{db_host}:5432/notion_bot'
    
    # Handle Heroku-style postgres:// URLs
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
    
    return database_url

def create_session():
    """Create database session"""
    engine = create_async_engine(get_database_url())
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) 