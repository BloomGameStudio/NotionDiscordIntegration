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


# Initialize DB and notion client
db = TinyDB("db.json")
notion_client = Client(auth=os.environ["NOTION_TOKEN"])


async def handle_updates(chan):
    logger.debug("Handle Updates")
    # Search all shared Notion databases and pages the bot has access to
    response = notion_client.search()
    results = response.get("results")

    for result in results:
        await handle_update(chan, result)
    return


async def handle_update(chan, result):
    # Compare result to previous results and Insert new results into db
    query = Query()
    # get the db rows that matches the id
    db_results = db.search(query.id == result.get("id"))

    if len(db_results) < 1:
        # No db Results
        db.insert(result)
        return

    last_db_result = db_results[-1]

    # Compare Last edited times
    if parser.parse(result.get("last_edited_time")) > parser.parse(
        last_db_result.get("last_edited_time")
    ):
        # We have a update

        title = notion_utils.get_page_title(result)
        # pprint(f"title:{title}")

        logger.debug("Getting the notion username of the last edited by")
        edited_by_user = notion_utils.get_username_by_id(
            result.get("last_edited_by").get("id")
        )
        logger.debug("Got the notion username of the last edited by")

        url = result.get("url")
        cover = result.get("cover", "No Cover Availabe")
        last_edited_time = parser.parse(result.get("last_edited_time")).strftime(
            "%d.%m.%Y %H:%M"
        )

        # print(f"{title} Update")
        # print(f"Edited By {edited_by_user}")

        # print(f"Update Info")
        # print("")
        # print(f"Title: {title}")
        # print(f"URL: {url}")
        # print(f"Cover: {cover}")
        # print(f"Last Edited Time: {last_edited_time}")
        # print(f"Last Edited By: {edited_by_user}")

        msg = f"""
                **__{title} Update__**
                Edited By: **{edited_by_user}**

                __Update Info__

                Title: {title}
                URL: {url}
                Cover: {cover}
                Last Edited Time: {last_edited_time}
                Last Edited By: {edited_by_user}
                """

        dedented_msg = textwrap.dedent(msg)
        await chan.send(dedented_msg)

    db.insert(result)

    # TODO: Prune db
    return
