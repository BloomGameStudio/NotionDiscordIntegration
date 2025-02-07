import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

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

# Create async engine
engine = None
if os.getenv("ENV") != "TEST":
    url = get_database_url().replace("postgres://", "postgresql+asyncpg://", 1)
    print(f"Connecting to {url}")

    engine = create_async_engine(
        url,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        echo=True
    )

Base = declarative_base()

def create_session():
    """Create database session"""
    if engine is None:
        raise RuntimeError("Database engine not initialized")
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def verify_database():
    """Verify database connection"""
    if engine is None:
        return
        
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        print("Successfully connected to the database!")
    except Exception as e:
        print(f"Failed to connect to database: {e}") 