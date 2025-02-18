#!/usr/bin/env python3
import json
import os
from datetime import datetime
from src.infrastructure.database.models import (
    NotionDocumentModel,
    NotionUserModel,
    NotionDocumentVersionModel,
)
from src.infrastructure.config.database import create_session
from src.utils.notion_utils import extract_title


def extract_clean_title(page: dict) -> str:
    """Extract clean title without IDs from page data"""
    if "properties" in page:
        for prop_name in ["Page", "Name", "Title"]:
            if prop_name in page["properties"]:
                title_prop = page["properties"][prop_name].get("title", [])
                if title_prop and isinstance(title_prop, list):
                    plain_text = title_prop[0].get("plain_text", "").strip()
                    if plain_text:
                        parts = plain_text.split()
                        if len(parts[-1]) == 32 and parts[-1].isalnum():
                            plain_text = " ".join(parts[:-1])
                        return plain_text

    if "title" in page:
        title_array = page["title"]
        if isinstance(title_array, list) and title_array:
            title = title_array[0].get("plain_text", "").strip()
            if title:
                return title

    return "Untitled Document"


def migrate_data(data=None, session_factory=None):
    """Migrate data from JSON to database"""
    if session_factory is None:
        session_factory = create_session()

    if data is None:
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "db.json"
        )
        try:
            with open(json_path, "r") as f:
                raw_data = json.load(f)
                if isinstance(raw_data, dict) and "_default" in raw_data:
                    data = list(raw_data["_default"].values())
                else:
                    data = raw_data
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in db.json")

    with session_factory() as session:
        with session.begin():
            users = set()
            for page in data:
                if page.get("object") != "page":
                    continue

                for user_type in ["created_by", "last_edited_by"]:
                    user = page.get(user_type, {})
                    if user and "id" in user:
                        users.add(
                            (
                                user["id"],
                                user.get("name", "Unknown User"),
                                user.get("avatar_url", ""),
                            )
                        )

            for user_id, name, avatar_url in users:
                try:
                    user = NotionUserModel(id=user_id, name=name, avatar_url=avatar_url)
                    session.add(user)
                except Exception as e:
                    # Skip if user already exists
                    session.rollback()
                    continue

            document_versions = {}
            for page in data:
                if page.get("object") != "page":
                    continue

                if not all(
                    key in page for key in ["id", "created_time", "last_edited_time"]
                ):
                    continue

                doc_id = page["id"]
                if doc_id not in document_versions:
                    document_versions[doc_id] = []
                document_versions[doc_id].append(page)

            for doc_id, versions in document_versions.items():
                versions.sort(
                    key=lambda x: datetime.fromisoformat(
                        x["last_edited_time"].replace("Z", "+00:00")
                    )
                )
                latest_version = versions[-1]

                doc = NotionDocumentModel(
                    id=doc_id,
                    object=latest_version.get("object", "page"),
                    created_time=datetime.fromisoformat(
                        versions[0]["created_time"].replace("Z", "+00:00")
                    ),
                    last_edited_time=datetime.fromisoformat(
                        latest_version["last_edited_time"].replace("Z", "+00:00")
                    ),
                    created_by_id=latest_version.get("created_by", {}).get("id"),
                    last_edited_by_id=latest_version.get("last_edited_by", {}).get(
                        "id"
                    ),
                    title=extract_title(latest_version),
                    url=latest_version.get("url", ""),
                    archived=latest_version.get("archived", False),
                    properties=latest_version.get("properties", {}),
                )
                session.add(doc)

                for version in versions:
                    version_record = NotionDocumentVersionModel(
                        document_id=doc_id,
                        object=version.get("object", "page"),
                        created_time=datetime.fromisoformat(
                            version["created_time"].replace("Z", "+00:00")
                        ),
                        last_edited_time=datetime.fromisoformat(
                            version["last_edited_time"].replace("Z", "+00:00")
                        ),
                        created_by_id=version.get("created_by", {}).get("id"),
                        last_edited_by_id=version.get("last_edited_by", {}).get("id"),
                        title=extract_title(version),
                        url=version.get("url", ""),
                        archived=version.get("archived", False),
                        properties=version.get("properties", {}),
                    )
                    session.add(version_record)

                print(f"Processed document with {len(versions)} versions: {doc.title}")


if __name__ == "__main__":
    migrate_data()
