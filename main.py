import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from handlers import (
    start,
    forward_to_group,
    forward_to_user,
    list_admins,
    add_admin,
    remove_admin,
    broadcast_start,
    broadcast_get_message,
    broadcast_get_buttons,
    broadcast_confirm_send,
    broadcast_cancel,
    GETTING_MESSAGE,
    GETTING_BUTTONS,
    CONFIRM_BROADCAST,
)
from settings import TELEGRAM_TOKEN, TELEGRAM_SUPPORT_CHAT_ID

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --- Set up all handlers ---
    
    # Broadcast conversation handler
    broadcast_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            GETTING_MESSAGE: [MessageHandler(filters.TEXT | filters.PHOTO, broadcast_get_message)],
            GETTING_BUTTONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_get_buttons)],
            CONFIRM_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_confirm_send)],
        },
        fallbacks=[CommandHandler("cancel", broadcast_cancel)],
    )
    application.add_handler(broadcast_conv_handler)
    
    # Admin management commands
    application.add_handler(CommandHandler("adminlist", list_admins))
    application.add_handler(CommandHandler("addadmin", add_admin))
    application.add_handler(CommandHandler("deladmin", remove_admin))
    
    # Core support bot handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(
        (filters.TEXT | filters.PHOTO) & ~filters.COMMAND & ~filters.Chat(chat_id=TELEGRAM_SUPPORT_CHAT_ID), 
        forward_to_group
    ))
    
    # --- THIS IS THE FIX ---
    # Simplified the filter to the most stable, common types to prevent the crash
    application.add_handler(MessageHandler(
        (filters.TEXT | filters.PHOTO | filters.VIDEO) & filters.REPLY & filters.Chat(chat_id=TELEGRAM_SUPPORT_CHAT_ID), 
        forward_to_user
    ))
    # ---------------------------

    logging.getLogger(__name__).info("Bot is starting with all features...")
    application.run_polling()

if __name__ == "__main__":
    main()
