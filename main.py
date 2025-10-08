# main.py

import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers import start, forward_to_group, forward_to_user, broadcast_message
from settings import TELEGRAM_TOKEN, TELEGRAM_SUPPORT_CHAT_ID

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["broadcast", "boardcast"], broadcast_message))
    
    application.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND & ~filters.Chat(chat_id=TELEGRAM_SUPPORT_CHAT_ID), forward_to_group))
    
    # This filter must accept TEXT, PHOTO, and VIDEO
    application.add_handler(MessageHandler(
        (filters.TEXT | filters.PHOTO | filters.VIDEO) & filters.REPLY & filters.Chat(chat_id=TELEGRAM_SUPPORT_CHAT_ID), 
        forward_to_user
    ))

    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
