from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from src.utils.notion_utils import extract_title


@dataclass
class NotionUser:
    id: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: dict) -> "NotionUser":
        """Create a NotionUser from API response data"""
        return cls(
            id=data["id"],
            name=data.get("name", "Unknown User"),
            avatar_url=data.get("avatar_url"),
        )


@dataclass
class NotionDocument:
    id: str
    object: str
    created_time: datetime
    last_edited_time: datetime
    created_by: NotionUser
    last_edited_by: NotionUser
    title: str
    url: Optional[str] = None
    archived: bool = False
    properties: Dict = None

    @classmethod
    def from_api_response(cls, data: dict) -> "NotionDocument":
        """Create a NotionDocument from API response data"""
        return cls(
            id=data["id"],
            object=data["object"],
            created_time=datetime.fromisoformat(
                data["created_time"].replace("Z", "+00:00")
            ),
            last_edited_time=datetime.fromisoformat(
                data["last_edited_time"].replace("Z", "+00:00")
            ),
            created_by=NotionUser.from_api_response(data["created_by"]),
            last_edited_by=NotionUser.from_api_response(data["last_edited_by"]),
            title=extract_title(data),
            url=data.get("url"),
            archived=data.get("archived", False),
            properties=data.get("properties", {}),
        )
