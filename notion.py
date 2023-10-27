import os
from notion_client import Client
import constants
from tinydb import TinyDB, Query
from datetime import datetime
from dateutil import parser
from utils import notion_utils
import asyncio
from my_logger import logger
import textwrap
from notion_client import AsyncClient
from datetime import timedelta

# Initialize DB and notion client
db = TinyDB("db.json")
notion_client = AsyncClient(auth=os.environ["NOTION_TOKEN"])
last_update_times = {}

async def fetch_all_results_from_notion():
    all_results = []
    start_cursor = None

    try:
        while True:
            response = await notion_client.search(page_size=100, start_cursor=start_cursor)
            results = response.get("results")
            all_results.extend(results)

            # If there's a next_cursor in the response, use it for the next request.
            # If not, break out of the loop.
            start_cursor = response.get("next_cursor")
            if not start_cursor:
                break

        return all_results

    except Exception as e:
        logger.error(f"Error fetching results from Notion: {e}")
        return all_results  # return whatever was fetched before the error


async def sync_db(db_lock) -> None:
    try:
        logger.debug("Starting Notion API search call.")
        results = await fetch_all_results_from_notion()
        logger.debug("Finished Notion API search call")
        
        async with db_lock:
            await asyncio.to_thread(db.insert_multiple, results)
            logger.debug(f"Data inserted into the database successfully")
    except Exception as e:
        logger.error(f"Error syncing database with Notion: {e}")


async def handle_creations(chan, db_lock):
    try:
        logger.debug("Handle Creation")
        results = await fetch_all_results_from_notion()
        
        # Collect all result IDs
        result_ids = [result.get("id") for result in results]

        # Fetch all IDs that exist in the database
        query = Query()
        async with db_lock:
            existing_ids = await asyncio.to_thread(db.search, query.id.test(lambda x: x in result_ids))
        existing_ids_set = {item['id'] for item in existing_ids}
        
        # Process only the results not in the database
        for result in results:
            if result.get("id") not in existing_ids_set:
                logger.debug("Processing results that are not in the database")
                await handle_creation(chan, result, db_lock)
    
    except Exception as e:
        logger.error(f"Error handling creations: {e}")

async def handle_creation(chan, result, db_lock):
    try:
        result_id = result.get("id")
        logger.debug(f"Handle Creation Result {result_id}")
        # Check for new creations
        query = Query()
        logger.debug("searching db for existing results")
        async with db_lock:
            db_results = await asyncio.to_thread(db.search, query.id == result.get("id"))

        if len(db_results) > 0:
            logger.debug("result already exists in db")
            return

        logger.debug("result does not exist in db")

        title = notion_utils.get_title(result)

        created_by_user = await notion_utils.get_username_by_id(
            result.get("created_by").get("id")
        )

        url = result.get("url")
        cover = result.get("cover", "No Cover Available")
        created_time_str = result.get("created_time")
        created_time_syntax = format_discord_timestamp(created_time_str)
        
        msg = f"""
                🧬 **__New {title}__** 🧬
                **Created By:** {created_by_user}
                **Title:** {title}
                **Date:** {created_time_syntax}
                **Link:** {url}
                """

        dedented_msg = textwrap.dedent(msg)
        logger.debug(f"Sending message to Discord:{dedented_msg}")
        await chan.send(dedented_msg)
        logger.debug(f"Message sent to Discord successfully")

        async with db_lock:
            await asyncio.to_thread(db.insert, result)
        logger.debug("Sent creation message and Inserted result into db")

    except Exception as e:
        logger.error(f"Error handling single creation: {e}")

async def handle_updates(chan, db_lock):
    try:
        logger.debug("Handle Updates")
        results = await fetch_all_results_from_notion()
        logger.debug(f"Total results after paginating: {len(results)}")
        logger.info(f"Total results after paginating: {len(results)}")    
        for result in results:
            await handle_update(chan, result, db_lock)
    except Exception as e:
        logger.error(f"Error handling updates: {e}")

async def handle_update(chan, result, db_lock):
    try:
        page_id = result.get("id")
        current_time = datetime.now()

        if page_id in last_update_times:
            last_update_time = last_update_times[page_id]
            time_difference = current_time - last_update_time
            if time_difference.total_seconds() < 3600:
                return

        last_update_times[page_id] = current_time
        query = Query()

        async with db_lock:
            db_results = await asyncio.to_thread(db.search, query.id == result.get("id"))

        if len(db_results) < 1:
            logger.info(f"No previous results found for {page_id}")
            return

        last_db_result = db_results[-1]
        result_last_edited_time = datetime.strptime(result.get("last_edited_time"), "%Y-%m-%dT%H:%M:%S.%fZ")
        last_db_result_last_edited_time = datetime.strptime(last_db_result.get("last_edited_time"), "%Y-%m-%dT%H:%M:%S.%fZ")
        
        if result_last_edited_time > last_db_result_last_edited_time:
            logger.debug(f"Updating {page_id}")

            title = notion_utils.get_title(result)
            edited_by_user = await notion_utils.get_username_by_id(
                result.get("last_edited_by").get("id")
            )

            url = result.get("url")
            cover = result.get("cover", "No Cover Available")
            last_edited_time_str = result.get("last_edited_time")
            last_edited_time_syntax = format_discord_timestamp(last_edited_time_str)
            
            msg = f"""
        📡**__{title} Update__**📡
        **Title:** {title}
        **Edited By:** {edited_by_user}
        **Date:** {last_edited_time_syntax}
        **Link:** {url}
        """

            dedented_msg = textwrap.dedent(msg)
            logger.debug(f"Sending message to Discord: {dedented_msg}")
            await chan.send(dedented_msg)
            logger.debug(f"Message sent to Discord successfully")

            async with db_lock:
                await asyncio.to_thread(db.insert, result)

    except Exception as e:
        logger.error(f"Error handling single update: {e}")

def format_discord_timestamp(time_str):
    timestamp = parser.parse(time_str)
    return f"<t:{int(timestamp.timestamp())}:d>"


if __name__ == "__main__":
    asyncio.run(handle_updates(1130461410871226368))