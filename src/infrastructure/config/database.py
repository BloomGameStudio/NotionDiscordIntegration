import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session


def get_database_url():
    """Get database URL from environment variables"""
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")

    DB_USER = os.getenv("DB_USER", "notion_bot")
    DB_NAME = os.getenv("DB_NAME", "notion_bot")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    if not DB_PASSWORD:
        raise ValueError("DB_PASSWORD environment variable is required")

    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"


Base = declarative_base()

engine = create_engine(
    "postgresql+psycopg2://notion_bot:notion_bot@localhost:5432/notion_bot",
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def create_session():
    """Create a new database session with automatic cleanup."""
    session = SessionLocal()
    try:
        return session
    finally:
        session.close()
