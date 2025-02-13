#!/usr/bin/env python3
from datetime import datetime, timedelta
from sqlalchemy import select, inspect, func

from src.infrastructure.database.models import (
    Base,
    NotionDocumentModel,
    NotionUserModel,
    NotionStateModel,
    NotionDocumentVersionModel,
)
from src.infrastructure.config.database import create_session


def query_documents(days_ago: int = 7):
    """Query documents modified in the last X days"""
    session_factory = create_session()
    try:
        with session_factory() as session:
            cutoff_date = datetime.now(datetime.UTC) - timedelta(days=days_ago)
            stmt = select(NotionDocumentModel).where(
                NotionDocumentModel.last_edited_time >= cutoff_date
            )
            result = session.execute(stmt)
            documents = result.scalars().all()

            print(f"\nDocuments modified in the last {days_ago} days:")
            print("-" * 50)
            for doc in documents:
                print(f"Title: {doc.title}")
                print(f"Last Edited: {doc.last_edited_time}")
                print(f"URL: {doc.url}")
                print(f"State: {doc.state.name if doc.state else 'No state'}")
                print(f"Created By: {', '.join(user.name for user in doc.created_by)}")
                print("-" * 50)
    except Exception as e:
        print(f"Error querying database: {e}")
        raise


def show_all_tables():
    """Show all tables in the database"""
    session_factory = create_session()
    engine = session_factory.kw["bind"]

    print("\nDatabase Tables:")
    with engine.begin() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        for table_name in tables:
            print(f"  - {table_name}")


def show_document_count():
    """Show count of documents"""
    session_factory = create_session()
    with session_factory() as session:
        doc_count = session.scalar(
            select(func.count()).select_from(NotionDocumentModel)
        )
        version_count = session.scalar(
            select(func.count()).select_from(NotionDocumentVersionModel)
        )
        print(f"\nDocument Count: {doc_count}")
        print(f"Version Count: {version_count}")


def show_recent_documents():
    """Show most recent documents"""
    session_factory = create_session()
    with session_factory() as session:
        query = (
            select(NotionDocumentModel)
            .order_by(NotionDocumentModel.last_edited_time.desc())
            .limit(5)
        )
        result = session.execute(query)
        documents = result.scalars().all()

        print("\nMost Recent Documents:")
        print("-" * 80)
        for doc in documents:
            print(f"ID: {doc.id}")
            print(f"Title: {doc.title}")
            print(f"Last Edited: {doc.last_edited_time}")
            print("-" * 80)


def show_document_versions(doc_id=None):
    """Show versions of documents"""
    session_factory = create_session()
    with session_factory() as session:
        if doc_id:
            query = (
                select(NotionDocumentVersionModel)
                .where(NotionDocumentVersionModel.document_id == doc_id)
                .order_by(NotionDocumentVersionModel.created_time)
            )
        else:
            query = (
                select(NotionDocumentVersionModel)
                .order_by(
                    NotionDocumentVersionModel.document_id,
                    NotionDocumentVersionModel.created_time,
                )
                .limit(10)
            )

        result = session.execute(query)
        versions = result.scalars().all()

        print("\nDocument Versions:")
        print("-" * 80)
        for v in versions:
            print(f"Document ID: {v.document_id}")
            print(f"Title: {v.title}")
            print(f"Created Time: {v.created_time}")
            print(f"Last Edited: {v.last_edited_time}")
            print("-" * 80)


def main():
    """Main function to show database information"""
    show_all_tables()
    show_document_count()
    show_recent_documents()
    show_document_versions()


if __name__ == "__main__":
    main()
