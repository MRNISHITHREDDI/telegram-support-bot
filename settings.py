import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("ERROR: TELEGRAM_TOKEN environment variable not set!")

try:
    TELEGRAM_SUPPORT_CHAT_ID = int(os.getenv("TELEGRAM_SUPPORT_CHAT_ID"))
except (ValueError, TypeError):
    raise ValueError("ERROR: TELEGRAM_SUPPORT_CHAT_ID is not a valid integer!")

try:
    OWNER_ID = int(os.getenv("OWNER_ID"))
except (ValueError, TypeError):
    raise ValueError("ERROR: OWNER_ID is not a valid integer!")
