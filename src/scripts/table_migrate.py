#!/usr/bin/env python3
from sqlalchemy import create_engine, select, Table
from sqlalchemy.orm import sessionmaker, Session
from src.infrastructure.database.models import (
    Base,
    NotionDocumentModel,
    NotionUserModel,
    NotionDocumentVersionModel,
    NotionStateModel,
)
from src.infrastructure.config.database import create_session
from src.utils.logging import logger


def migrate_tables(source_url: str, target_session_factory=None):
    """Migrate data from source database to target database"""
    if target_session_factory is None:
        target_session_factory = create_session()

    # Create source engine and session
    source_engine = create_engine(source_url)
    source_session_factory = sessionmaker(
        source_engine, class_=Session, expire_on_commit=False
    )

    try:
        with source_session_factory() as source_session, target_session_factory() as target_session:
            with target_session.begin():
                # First migrate users since they're referenced by other tables
                logger.info("Migrating users...")
                user_stmt = select(NotionUserModel)
                users = source_session.execute(user_stmt).scalars().all()
                for user in users:
                    target_session.merge(user)

                # Migrate association tables
                logger.info("Migrating document creators associations...")
                creators_table = Table(
                    "notion_document_creators", Base.metadata, extend_existing=True
                )
                creators_data = source_session.execute(select(creators_table)).all()
                for row in creators_data:
                    target_session.execute(
                        creators_table.insert().values(
                            document_id=row.document_id, user_id=row.user_id
                        )
                    )

                logger.info("Migrating document assignees associations...")
                assignees_table = Table(
                    "notion_document_assignees", Base.metadata, extend_existing=True
                )
                assignees_data = source_session.execute(select(assignees_table)).all()
                for row in assignees_data:
                    target_session.execute(
                        assignees_table.insert().values(
                            document_id=row.document_id, user_id=row.user_id
                        )
                    )

                # Migrate documents
                logger.info("Migrating documents...")
                doc_stmt = select(NotionDocumentModel)
                documents = source_session.execute(doc_stmt).scalars().all()
                for doc in documents:
                    target_session.merge(doc)

                # Migrate document versions
                logger.info("Migrating document versions...")
                version_stmt = select(NotionDocumentVersionModel)
                versions = source_session.execute(version_stmt).scalars().all()
                for version in versions:
                    target_session.merge(version)

                # Migrate state
                logger.info("Migrating state...")
                state_stmt = select(NotionStateModel)
                states = source_session.execute(state_stmt).scalars().all()
                for state in states:
                    target_session.merge(state)

        logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise


if __name__ == "__main__":
    import os

    source_db_url = os.getenv("SOURCE_DATABASE_URL")
    if not source_db_url:
        raise ValueError("SOURCE_DATABASE_URL environment variable must be set")

    migrate_tables(source_db_url)
