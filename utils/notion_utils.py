from notion_client import Client
import os

notion = Client(auth=os.environ["NOTION_TOKEN"])


def get_user_by_id(id):
    user = notion.users.retrieve(id)
    return user


def get_username_by_id(id):
    name = get_user_by_id(id).get("name")
    return name

def get_page_title(page):
    _properties = page.get("properties")
    # pprint(f"properties: {_properties}")

    _Name = _properties.get("Page")
    # pprint(f"Name:{_Name}")

    _title = _Name.get("title")[0]
    # pprint(f"_title:{_title}")

    _plain_text = _title.get("plain_text")
    # pprint(f"_plain_text:{_plain_text}")

    _text = _title.get("text")
    # pprint(f"_text:{_text}")

    title = _text.get("content")
    # pprint(f"title:{title}")

    return title

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
