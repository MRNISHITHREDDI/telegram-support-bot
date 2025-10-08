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
    broadcast_start,
    broadcast_get_message,
    broadcast_get_buttons,
    broadcast_confirm_send,
    broadcast_cancel,
    GETTING_MESSAGE,
    GETTING_BUTTONS,
    CONFIRM_BROADCAST,
    # Import new admin functions
    list_admins,
    add_admin,
    remove_admin,
)
from settings import TELEGRAM_TOKEN, TELEGRAM_SUPPORT_CHAT_ID

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Conversation handler for broadcast
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            GETTING_MESSAGE: [MessageHandler(filters.TEXT | filters.PHOTO, broadcast_get_message)],
            GETTING_BUTTONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_get_buttons)],
            CONFIRM_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_confirm_send)],
        },
        fallbacks=[CommandHandler("cancel", broadcast_cancel)],
    )
    application.add_handler(conv_handler)
    
    # --- ADD NEW ADMIN COMMANDS ---
    application.add_handler(CommandHandler("adminlist", list_admins))
    application.add_handler(CommandHandler("addadmin", add_admin))
    application.add_handler(CommandHandler("deladmin", remove_admin))
    # ----------------------------
    
    # Add other handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND & ~filters.Chat(chat_id=TELEGRAM_SUPPORT_CHAT_ID), forward_to_group))
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.Chat(chat_id=TELEGRAM_SUPPORT_CHAT_ID), forward_to_user))

    logging.getLogger(__name__).info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
