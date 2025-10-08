import os
from dotenv import load_dotenv

load_dotenv()

# Correctly uses the NAME of the variable
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("ERROR: TELEGRAM_TOKEN environment variable not set in Railway!")

try:
    # Correctly uses the NAME of the variable
    TELEGRAM_SUPPORT_CHAT_ID = int(os.getenv("TELEGRAM_SUPPORT_CHAT_ID"))
except (ValueError, TypeError):
    raise ValueError("ERROR: TELEGRAM_SUPPORT_CHAT_ID not set or is not a number in Railway!")

try:
    # Correctly uses the NAME of the variable
    OWNER_ID = int(os.getenv("OWNER_ID"))
except (ValueError, TypeError):
    raise ValueError("ERROR: OWNER_ID not set or is not a number in Railway!")
