#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from src.infrastructure.config.database import create_session
from src.infrastructure.database.models import Base
from src.utils.logging import logger

async def clear_database():
    """Clear all data from the database while preserving the schema"""
    session_factory = create_session()
    engine = session_factory.kw['bind']
    
    try:
        async with engine.begin() as conn:
            # Get all table names
            tables = Base.metadata.sorted_tables
            
            # Disable trigger constraints temporarily
            await conn.execute(text("SET session_replication_role = 'replica';"))
            
            # Truncate all tables in a single transaction
            for table in tables:
                logger.info(f"Clearing table: {table.name}")
                await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE;"))
            
            # Re-enable trigger constraints
            await conn.execute(text("SET session_replication_role = 'origin';"))
            
        logger.info("Database cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(clear_database())