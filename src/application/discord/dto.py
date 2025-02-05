from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class ChannelDTO:
    """Data transfer object for Discord channels"""
    id: int
    name: str
    guild_id: int

@dataclass
class BotStateDTO:
    """Data transfer object for bot state"""
    start_time: datetime
    last_heartbeat: datetime
    connected_channels: List[ChannelDTO] 