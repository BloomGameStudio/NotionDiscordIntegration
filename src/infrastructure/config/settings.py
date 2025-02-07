from dotenv import load_dotenv
import os
from dataclasses import dataclass
from typing import List
from .constants import COLLECTIVE_DB, NOTION_NOTIFICATION_CHANNELS
from src.infrastructure.config.database import get_database_url


@dataclass
class Settings:
    """Application settings loaded from environment variables and constants"""

    NOTION_TOKEN: str
    DISCORD_BOT_TOKEN: str

    DATABASE_URL: str

    NOTION_DATABASE_ID: str
    NOTION_NOTIFICATION_CHANNELS: List[int]

    UPDATE_INTERVAL: int = 10
    AGGREGATE_UPDATE_INTERVAL: int = 60 * 60 * 24
    UPDATE_COOLDOWN: int = 14400

    def __init__(self):
        load_dotenv()

        self.NOTION_TOKEN = os.getenv("NOTION_TOKEN")
        self.DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
        self.DATABASE_URL = get_database_url()
        self.NOTION_DATABASE_ID = os.getenv(
            "NOTION_DATABASE_ID", "07752fd5ba8e44c7b8e48bfee50f0545"
        )

        channels_str = os.getenv("NOTION_NOTIFICATION_CHANNELS", "")
        self.NOTION_NOTIFICATION_CHANNELS = [
            int(channel.strip())
            for channel in channels_str.split(",")
            if channel.strip()
        ] or NOTION_NOTIFICATION_CHANNELS

    @classmethod
    def load_from_env(cls) -> "Settings":
        """Load settings from environment variables"""
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://notion_bot:notion_bot@localhost:5432/notion_bot",
        )

        return cls(
            NOTION_TOKEN=os.environ["NOTION_TOKEN"],
            DISCORD_BOT_TOKEN=os.environ["DISCORD_BOT_TOKEN"],
            DATABASE_URL=database_url,
            NOTION_DATABASE_ID=COLLECTIVE_DB,
            NOTION_NOTIFICATION_CHANNELS=NOTION_NOTIFICATION_CHANNELS,
        )


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
        raise ValueError("At least one notification channel is required")
