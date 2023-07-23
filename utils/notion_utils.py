from notion_client import Client
import os

notion = Client(auth=os.environ["NOTION_TOKEN"])


def get_user_by_id(id):
    user = notion.users.retrieve(id)
    return user


def get_username_by_id(id):
    name = get_user_by_id(id).get("name")
    return name
