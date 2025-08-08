import os
from dotenv import load_dotenv

load_dotenv()

SAMPLE_ID = os.getenv('SAMPLE_ID')
AI_ASSISTANT_FOR_TELEGRAM_BOT_ID = os.getenv('AI_ASSISTANT_FOR_TELEGRAM_BOT_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
FIGMA_API_TOKEN = os.getenv('FIGMA_API_TOKEN')
FIGMA_FILE_KEY = os.getenv('FIGMA_FILE_KEY')
OWNER_ID = os.getenv('OWNER_ID')
BOT_TOKEN = os.getenv('BOT_TOKEN')
