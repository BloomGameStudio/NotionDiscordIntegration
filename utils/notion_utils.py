from notion_client import Client
import os
from pprint import pprint
from my_logger import logger

notion = Client(auth=os.environ["NOTION_TOKEN"])


def get_user_by_id(id):
    user = notion.users.retrieve(id)
    return user


def get_username_by_id(id):
    name = get_user_by_id(id).get("name")
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

    return "No Title Availabe"


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
