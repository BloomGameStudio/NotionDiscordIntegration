#!/usr/bin/env python3
from src.infrastructure.config.database import engine
from src.infrastructure.database.models import Base
from src.utils.logging import logger


def init_db():
    """Initialize database tables"""
    logger.info("Initializing database tables")
    Base.metadata.create_all(engine)
    engine.dispose()
    logger.info("Database tables initialized successfully")


if __name__ == "__main__":
    init_db()
