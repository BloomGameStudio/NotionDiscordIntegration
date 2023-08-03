import re
from helpers import find_nested_dict_key
from notion_client import AsyncClient
import os
from pprint import pprint
from my_logger import logger
from typing import Union


notion = AsyncClient(auth=os.environ["NOTION_TOKEN"])


async def get_user_by_id(id):
    logger.debug("Getting the notion user by id")
    user = await notion.users.retrieve(id)
    logger.debug("Returning Notion user by id")
    return user


async def get_username_by_id(id):
    logger.debug("Getting the notion username by id")
    try:
        user = await get_user_by_id(id)
        name = user.get("name")
    except AttributeError as e:
        logger.error(f"Error getting the notion username by id: {e}")
        logger.exception(e)
        raise e

    logger.debug("Returning Notion username by id")
    return name


def get_page_title(page):
    try:
        _properties = page.get("properties")
        # pprint(f"properties: {_properties}")

        try:
            _Name = _properties.get("Name")
            # pprint(f"Name:{_Name}")
            _title = _Name.get("title")[0]
            # pprint(f"_title:{_title}")
        except AttributeError as e:
            pass

        try:
            _Page = _properties.get("Page")
            # pprint(f"Page:{_Page}")
            _title = _Page.get("title")[0]
            # pprint(f"_title:{_title}")
        except AttributeError as e:
            pass

        _plain_text = _title.get("plain_text")
        # pprint(f"_plain_text:{_plain_text}")

        _text = _title.get("text")
        # pprint(f"_text:{_text}")

        title = _text.get("content")
        # pprint(f"title:{title}")
        return title

    except:
        pass

    return "No Title Available"


def get_page_plain_text_title(page):
    _properties = page.get("properties")
    # pprint(f"properties: {_properties}")

    _Name = _properties.get("Page")
    # pprint(f"Name:{_Name}")

    _title = _Name.get("title")[0]
    # pprint(f"_title:{_title}")

    plain_text = _title.get("plain_text")
    # pprint(f"_plain_text:{_plain_text}")

    return plain_text


def get_database_title(database) -> str:
    """
    Purpose:
    """

    _title = database.get("title")[0]
    plain_text = _title.get("plain_text")
    return plain_text


# end def


def get_title(document: Union[list, dict]) -> str:
    plain_text = find_nested_dict_key(document, "plain_text")
    return plain_text or "No Title Available"


if __name__ == "__main__":
    from notion_client import Client

    notion_client = Client(auth=os.environ["NOTION_TOKEN"])
    search = notion_client.search()
    results = search.get("results")
