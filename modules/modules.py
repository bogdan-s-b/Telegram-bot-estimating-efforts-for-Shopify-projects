import datetime
import os
import re
import sys
import signal
import openai
from openai import AsyncOpenAI
import asyncio



import tempfile

# from langchain.llms import OpenAI
# from langchain.agents import load_tools
# from langchain.agents import initialize_agent

from pprint import pprint

from functools import partial

import io
from io import BytesIO
import telegram.ext
import json
import requests
from collections import defaultdict
import time

from GoogleDocsAPI import GoogleDocsService
from FigmaAPI import FigmaDataExtractor

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Bot,
)

from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    PicklePersistence
)

from secrets import *

# os.environ["HTTP_PROXY"] = "http://8.8.8.8:80"
# os.environ["HTTPS_PROXY"] = "http://8.8.8.8:80"

CAN_PRINT = False

CONTINUE = 1
COLLECT = 2

EDIT = (1 << 0)
SEND = (1 << 1)

SESSION_DURATION = datetime.timedelta(hours=24)
SUPPORTED_EXTENSIONS = {
    "photo": ".jpg",
    "document": ".pdf",
    "audio": ".mp3",
    "voice": ".mp3",
    "video": ".mp4",
    "sticker": ".png"
}

PRIME_A = 31
PRIME_B = 10_000_000_019
