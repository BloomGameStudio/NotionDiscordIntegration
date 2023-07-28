import discord
import os
import asyncio
import notion
from my_logger import logger
from constants import NOTION_NOTIFICATION_CHANNEL


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        self.db_lock = asyncio.Lock()
        # create the background tasks and run it in the background
        self.notion_creation_task = self.loop.create_task(
            self.notion_creation_notifications()
        )

        self.notion_update_task = self.loop.create_task(
            self.notion_updates_notifications()
        )

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("------")

    async def notion_updates_notifications(self):
        await self.wait_until_ready()
        channel = self.get_channel(NOTION_NOTIFICATION_CHANNEL)
        while not self.is_closed():
            await notion.handle_updates(channel, self.db_lock)
            logger.info("Notion updates handled")
            await asyncio.sleep(10)  # task runs every x seconds

    async def notion_creation_notifications(self):
        await self.wait_until_ready()
        channel = self.get_channel(NOTION_NOTIFICATION_CHANNEL)
        while not self.is_closed():
            await notion.handle_creations(channel)
            await asyncio.sleep(5)  # task runs every x seconds


intents = discord.Intents.default()

client = MyClient(intents=intents)

client.run(os.environ["DISCORD_BOT_TOKEN"])
