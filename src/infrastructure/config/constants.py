from datetime import timedelta

# Notion Database IDs
COLLECTIVE_DB = "07752fd5ba8e44c7b8e48bfee50f0545"

# Discord Channel IDs
NOTION_NOTIFICATION_CHANNELS = [
    1199565796242890843
]

# Date Formats
DATE_FMT = "%d %m %Y %H:%M"

# Time Constants
WEEKLY_UPDATE_INTERVAL = timedelta(days=7)
DEFAULT_RETRY_DELAY = 1
DEFAULT_RETRY_BACKOFF = 2
MAX_RETRY_ATTEMPTS = 3

# Database Constants
MAX_BATCH_SIZE = 100
DEFAULT_PAGE_SIZE = 50

# Message Templates
MESSAGE_TEMPLATES = {
    "update": "📡**__{title} Update__**📡",
    "creation": "🎉 **New Entry Created: {title}**",
    "weekly_summary": "📊 **Weekly Notion Update Summary**"
} 