import discord
import os
import asyncio
import notion
import datetime
import json
from my_logger import logger
from constants import NOTION_NOTIFICATION_CHANNEL


class MyClient(discord.Client):
    START_TIME_FILE = "./start_time.json"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        self.db_lock = asyncio.Lock()

        # create the background tasks and run them in the background
        self.notion_creation_task = self.loop.create_task(
            self.notion_creation_notifications()
        )

        self.notion_update_task = self.loop.create_task(
            self.notion_updates_notifications()
        )

        self.notion_aggregate_updates_task = self.loop.create_task(
            self.notion_aggregate_updates_notifications()
        )

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("------")

        if not os.path.exists(MyClient.START_TIME_FILE):
            self.save_start_time()

    def save_start_time(self):
        start_time = datetime.datetime.utcnow()
        try:
            with open(MyClient.START_TIME_FILE, "w") as file:
                json.dump({"start_time": start_time.isoformat()}, file)
        except Exception as e:
            logger.error(f"Error saving start time: {e}")

    def load_start_time(self):
        try:
            if os.path.exists(MyClient.START_TIME_FILE):
                with open(MyClient.START_TIME_FILE, "r") as file:
                    data = file.read()
                    if data:
                        return datetime.datetime.fromisoformat(
                            json.loads(data)["start_time"]
                        )
        except Exception as e:
            logger.error(f"Error loading start time: {e}")

        # If the file doesn't exist or is empty, save the start time
        logger.info("No start time found. Saving start time.")
        self.save_start_time()
        return None

    async def notion_updates_notifications(self):
        await self.wait_until_ready()
        channel = self.get_channel(NOTION_NOTIFICATION_CHANNEL)
        while not self.is_closed():
            await notion.handle_updates(channel, self.db_lock)
            logger.info("Notion updates handled")
            await asyncio.sleep(10)  # task runs every x seconds

    async def notion_creation_notifications(self):
        await self.wait_until_ready()

        await notion.sync_db(self.db_lock)

        channel = self.get_channel(NOTION_NOTIFICATION_CHANNEL)
        while not self.is_closed():
            await notion.handle_creations(channel, self.db_lock)
            logger.info("Notion Creations handled")
            await asyncio.sleep(10)  # task runs every x seconds

    async def notion_aggregate_updates_notifications(self):
        await self.wait_until_ready()

        channel = self.get_channel(NOTION_NOTIFICATION_CHANNEL)

        while not self.is_closed():
            start_time = self.load_start_time()
            logger.info(f"Start time: {start_time}")
            if start_time:
                time_difference = datetime.datetime.utcnow() - start_time
                logger.info(f"Time difference: {time_difference}")
                days_passed = time_difference.days

                if days_passed >= 7:
                    await notion.handle_aggregate_updates(channel, self)
                    logger.info("Notion Aggregate Updates Handled")

                    # Reset start time for next 7-day cycle
                    self.save_start_time()
            await asyncio.sleep(60 * 60 * 24)

intents = discord.Intents.default()

client = MyClient(intents=intents)

client.run(os.environ["DISCORD_BOT_TOKEN"])