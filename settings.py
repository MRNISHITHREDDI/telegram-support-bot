# settings.py

import os
from dotenv import load_dotenv

load_dotenv()

# Your bot's token from @BotFather
TELEGRAM_TOKEN = os.getenv("8323491619:AAErBPaV7dgTU0TxL75pd37lDDxQvwcHZkI")

# The chat ID of your private support GROUP
TELEGRAM_SUPPORT_CHAT_ID = int(os.getenv("-1003194535937"))

# The ID of the bot's owner (Super Admin). Only this user can add/remove other admins.
# Find your ID by messaging @userinfobot.
OWNER_ID = int(os.getenv("7577482514"))
