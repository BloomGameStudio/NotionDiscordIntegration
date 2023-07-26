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
