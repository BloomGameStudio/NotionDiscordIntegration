import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from datetime import datetime, timezone, timedelta
from src.application.discord.discord_service import DiscordService
from unittest.mock import AsyncMock
from src.application.notion.dto import NotificationMessage
import asyncio

@pytest.mark.asyncio
async def test_handle_aggregate_updates():
    # Mock data
    start_time = datetime.now(timezone.utc) - timedelta(days=8)
    
    async def mock_handle_aggregate_updates(self, start_time):
        return NotificationMessage(
            title='Weekly Summary',
            content='Test update',
            timestamp=datetime.now(timezone.utc),
            channels=[123456789]
        )
    
    notion_service = type('MockNotionService', (), {
        'handle_aggregate_updates': mock_handle_aggregate_updates
    })()
    
    service = DiscordService(
        notion_service=notion_service,
        settings=type('MockSettings', (), {'NOTION_TOKEN': 'test-token'})()
    )
    service._start_time = start_time
    
    notification = await service.handle_aggregate_updates()
    assert notification is not None
    assert notification.title == 'Weekly Summary'

@pytest.mark.asyncio
async def test_handle_update_notifications():
    mock_notification = NotificationMessage(
        title="Test", 
        content="Update",
        timestamp=datetime.now(timezone.utc),
        channels=[123456789]
    )
    notion_service = type('MockNotionService', (), {
        'handle_updates': AsyncMock(return_value=[mock_notification])
    })()
    
    service = DiscordService(notion_service=notion_service, settings=None)
    notifications = await service.handle_update_notifications()
    assert len(notifications) == 1
    assert notifications[0].title == "Test"

@pytest.mark.asyncio
async def test_handle_update_notifications_error():
    notion_service = type('MockNotionService', (), {
        'handle_updates': AsyncMock(side_effect=Exception("Test error"))
    })()
    
    service = DiscordService(notion_service=notion_service, settings=None)
    notifications = await service.handle_update_notifications()
    assert len(notifications) == 0

@pytest.mark.asyncio
async def test_lock_mechanism():
    notion_service = type('MockNotionService', (), {
        'handle_updates': AsyncMock(return_value=[])
    })()
    
    service = DiscordService(notion_service=notion_service, settings=None)
    
    # Create two concurrent tasks
    async def task1():
        return await service.handle_update_notifications()
        
    async def task2():
        return await service.handle_update_notifications()
    
    # Run tasks concurrently with a timeout
    async with asyncio.timeout(2.0):  # Add timeout to prevent hanging
        results = await asyncio.gather(task1(), task2())
    
    assert len(results) == 2  # Both tasks should complete