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
import os
from pprint import pprint

# Initialize DB and notion client
db = TinyDB("db.json")
notion_client = AsyncClient(auth=os.environ["NOTION_TOKEN"])
