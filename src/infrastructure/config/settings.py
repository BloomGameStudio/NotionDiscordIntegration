from dotenv import load_dotenv
import os
from dataclasses import dataclass
from typing import List
from .constants import NOTION_NOTIFICATION_CHANNELS


@dataclass
class Settings:
    """Application settings loaded from environment variables and constants"""

    STORAGE_CONNECTION_STRING: str
    STORAGE_TABLE_NAME: str
    NOTION_TOKEN: str
    DISCORD_BOT_TOKEN: str
    NOTION_DATABASE_ID: str
    NOTION_NOTIFICATION_CHANNELS: List[int]

    UPDATE_INTERVAL: int = 10
    AGGREGATE_UPDATE_INTERVAL: int = 60 * 60 * 24
    UPDATE_COOLDOWN: int = 14400

    def __init__(self):
        load_dotenv()

        self.STORAGE_CONNECTION_STRING = os.getenv(
            "STORAGE_CONNECTION_STRING",
            os.getenv("AzureWebJobsStorage", ""),
        )
        self.STORAGE_TABLE_NAME = os.getenv("STORAGE_TABLE_NAME", "notionDocuments")
        self.NOTION_TOKEN = os.getenv("NOTION_TOKEN")
        self.DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
        self.NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
        self.NOTION_NOTIFICATION_CHANNELS = [
            int(channel.strip())
            for channel in os.getenv("NOTION_NOTIFICATION_CHANNELS", "").split(",")
            if channel.strip()
        ] or NOTION_NOTIFICATION_CHANNELS

    @classmethod
    def load_from_env(cls) -> "Settings":
        """Load settings from environment variables"""
        return cls()


def load_environment() -> Settings:
    """Load environment variables into Settings object"""
    return Settings()


def validate_settings(settings: Settings) -> None:
    """Validate required settings"""
    if not settings.NOTION_TOKEN:
        raise ValueError("NOTION_TOKEN is required")
    if not settings.DISCORD_BOT_TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN is required")
    if not settings.NOTION_DATABASE_ID:
        raise ValueError("NOTION_DATABASE_ID is required")
    if not settings.NOTION_NOTIFICATION_CHANNELS:
        raise ValueError("At least one NOTION_NOTIFICATION_CHANNELS value is required")
    if not settings.STORAGE_CONNECTION_STRING:
        raise ValueError(
            "STORAGE_CONNECTION_STRING or AzureWebJobsStorage is required"
        )
