from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class NotionUpdateDTO:
    """Data transfer object for Notion updates"""

    document_id: str
    title: str
    edited_by: str
    edited_time: datetime
    url: Optional[str] = None


@dataclass
class NotificationMessage:
    """Data transfer object for notification messages"""

    title: str
    content: str
    timestamp: datetime
    channels: List[int]
