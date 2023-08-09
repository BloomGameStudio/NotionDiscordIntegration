# NOTE:
# Doing either of the below examples wont work the discord message wont be send

# results = await asyncio.gather(*[handle_update(chan, result) for result in results])

# try:
#     async with asyncio.TaskGroup() as tg:
#         try:
#             for result in results:
#                 tg.create_task(handle_update(chan, result))
#         except Exception as e:
#             logger.error(e)
#             raise e
# except Exception as e:
#     logger.error(e)
#     raise e


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


async def sync_db(db_lock) -> None:
    """
    Sync the db with Notion
    """
    response = await notion_client.search()
    results = response.get("results")

    async with db_lock:
        # Insert new results into
        await asyncio.to_thread(db.insert_multiple, results)

    return


# end def


async def handle_creations(chan, db_lock):
    logger.debug("Handle Creation")
    # Search all shared Notion databases and pages the bot has access to
    response = await notion_client.search()
    results = response.get("results")

    for result in results:
        await handle_creation(chan, result, db_lock)
    return


async def handle_creation(chan, result, db_lock):
    result_id = result.get("id")
    logger.debug(f"Handle Creation Result {result_id}")
    # Check for new creations
    query = Query()
    logger.debug("searching db for existing results")
    async with db_lock:
        # get the db rows that matches the id
        db_results = await asyncio.to_thread(db.search, query.id == result.get("id"))
        # db_results = db.search(query.id == result.get("id"))

    if len(db_results) > 0:
        logger.debug("result already exists in db")
        # result already exists in db
        return

    logger.debug("result does not exist in db")

    # We have a creation

    title = notion_utils.get_title(result)
    # pprint(f"title:{title}")

    created_by_user = await notion_utils.get_username_by_id(
        result.get("created_by").get("id")
    )

    url = result.get("url")
    cover = result.get("cover", "No Cover Available")
    created_time = parser.parse(result.get("created_time")).strftime("%d.%m.%Y %H:%M")

    msg = f"""
            🧬 **__New {title}__** 🧬
            **Created By:** {created_by_user}
            **Title:** {title}
            **Time:** {created_time}
            **Link:** {url}
            """

    dedented_msg = textwrap.dedent(msg)
    await chan.send(dedented_msg)

    async with db_lock:
        # Insert new results into
        await asyncio.to_thread(db.insert, result)
        # db.insert(result)

    logger.debug("Sent creation message and Inserted result into db")
    return


async def handle_updates(chan, db_lock):
    logger.debug("Handle Updates")
    # Search all shared Notion databases and pages the bot has access to
    response = await notion_client.search()
    results = response.get("results")
    # logger.debug(results)
    logger.debug(f"Results len: {len(results)}")

    for result in results:
        await handle_update(chan, result, db_lock)
    return


async def handle_update(chan, result, db_lock):
    # logger.info("Handling Notion Update")

    # Compare result to previous results and Insert new results into db
    query = Query()

    async with db_lock:
        # get the db rows that matches the id
        db_results = await asyncio.to_thread(db.search, query.id == result.get("id"))
        # db_results = db.search(query.id == result.get("id"))

    # logger.debug(f"DB Results: {db_results}")

    if len(db_results) < 1:
        # async with db_lock:
        #     # No db Results
        #     await asyncio.to_thread(db.insert, result)
        #     # db.insert(result)
        return

    last_db_result = db_results[-1]

    # logger.debug(f"Last DB Result: {last_db_result}")

    # Compare Last edited times
    if parser.parse(result.get("last_edited_time")) > parser.parse(
        last_db_result.get("last_edited_time")
    ):
        # We have a update
        logger.debug("We have a update")

        title = notion_utils.get_title(result)
        # pprint(f"title:{title}")

        logger.debug("Getting the notion username of the last edited by")
        edited_by_user = await notion_utils.get_username_by_id(
            result.get("last_edited_by").get("id")
        )
        logger.debug("Got the notion username of the last edited by")

        url = result.get("url")
        cover = result.get("cover", "No Cover Available")
        last_edited_time = parser.parse(result.get("last_edited_time")).strftime(
            "%d.%m.%Y %H:%M"
        )
        logger.debug("Building MSG")

        msg = f"""
                📡**__{title} Update__**📡
                **Title:** {title}
                **Edited By:** {edited_by_user}
                **Time:** {last_edited_time}
                **Link:** {url}
                """

        dedented_msg = textwrap.dedent(msg)

        logger.debug("Sending Dedented Message to Chan")
        await chan.send(dedented_msg)
        logger.debug("Sent Dedented Message to Chan")

        async with db_lock:
            await asyncio.to_thread(db.insert, result)
            # db.insert(result)

        # TODO: Prune db

    return


async def handle_aggregate_updates(chan):
    try:
        logger.debug("Handle Aggregate Updates")

        # Calculate the date 7 days ago from today in UTC
        seven_days_ago_timestamp = int((datetime.now() - timedelta(days=7)).timestamp())
        # Search all shared Notion databases and pages the bot has access to
        response = await notion_client.search()
        results = response.get("results")
        logger.debug(f"Results len: {len(results)}")

        # Initialize an empty list to store aggregated changes
        aggregated_changes = []

        for result in results:
            properties = result.get("properties")
            if properties:
                tags_property = properties.get("Tags")
                if tags_property and tags_property.get("type") == "multi_select":
                    tags_options = tags_property.get("multi_select", [])

                    # Check if tags_options is a list of dictionaries or a dictionary with "options" key
                    if isinstance(tags_options, list):
                        # Handle the case where tags_options is a list of dictionaries
                        if any(
                            option.get("name") == "Digest" for option in tags_options
                        ):
                            last_edited_timestamp = parser.parse(
                                result.get("last_edited_time")
                            ).timestamp()
                            if last_edited_timestamp >= seven_days_ago_timestamp:
                                aggregated_changes.append(result)
                    elif isinstance(tags_options, dict) and "options" in tags_options:
                        # Handle the case where tags_options is a dictionary with an "options" key
                        if any(
                            option["name"] == "Digest"
                            for option in tags_options["options"]
                        ):
                            last_edited_time = parser.parse(
                                result.get("last_edited_time")
                            )
                            last_edited_timestamp = last_edited_time.timestamp()
                            if last_edited_timestamp >= seven_days_ago_timestamp:
                                aggregated_changes.append(result)
                else:
                    logger.debug("No multi_select tags options in properties")
            else:
                logger.debug("No properties found in result")

        # Check if there are aggregated changes to send
        if len(aggregated_changes) > 0:
            # Create a Discord message with the aggregated changes
            msg = "📆 **__Aggregate Changes in the Last 7 Days__** 📆\n\n"
            messages = []
            current_msg = msg

            for result in aggregated_changes:
                title = notion_utils.get_title(result)
                edited_by_user = await notion_utils.get_username_by_id(
                    result.get("last_edited_by").get("id")
                )
                url = result.get("url")
                last_edited_time = parser.parse(
                    result.get("last_edited_time")
                ).strftime("%d.%m.%Y %H:%M")

                change_details = f"""
            **Title:** {title}
            **Edited By:** {edited_by_user}
            **Time:** {last_edited_time}
            **Link:** {url}
            """

                change_details = "\n".join(
                    line.lstrip() for line in change_details.strip().split("\n")
                )
                # If adding the current change to the current message would exceed the limit, send the current message
                if len(current_msg) + len(change_details) > 1999:
                    messages.append(current_msg)
                    current_msg = msg

                current_msg += change_details + "\n"

            # Add the last message to the list of messages
            if current_msg != msg:
                messages.append(current_msg)

            # Send all the messages
            for message in messages:
                dedented_msg = textwrap.dedent(message)
                await chan.send(dedented_msg)
    except Exception as e:
        logger.error(f"An error occurred: {e}")

    return


if __name__ == "__main__":
    asyncio.run(handle_updates(1130461410871226368))
