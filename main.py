import os
from notion_client import Client
from pprint import pprint


notion = Client(auth=os.environ["NOTION_TOKEN"])
