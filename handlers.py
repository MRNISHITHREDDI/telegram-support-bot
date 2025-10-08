import asyncio
import os
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest
from settings import TELEGRAM_SUPPORT_CHAT_ID, ADMIN_IDS
import logging

# (The top part of the file with save_user_id, start, and broadcast_message remains the same)
logger = logging.getLogger(__name__)
USER_IDS_FILE = "user_ids.txt"
WELCOME_PHOTO_ID_FILE = "welcome_photo_id.txt"

def save_user_id(user_id: int):
    # ... (function is correct)
    try:
        if os.path.exists(USER_IDS_FILE):
            with open(USER_IDS_FILE, "r") as f:
                existing_ids = set(line.strip() for line in f)
        else:
            existing_ids = set()
        existing_ids.add(str(user_id))
        with open(USER_IDS_FILE, "w") as f:
            for uid in sorted(existing_ids, key=int):
                f.write(uid + "\n")
    except Exception as e:
        logger.error(f"Error saving user ID {user_id}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (function is correct)
    user = update.effective_user
    save_user_id(user.id)
    caption_text = f"👋 Welcome! How can we help you today? {user.first_name}"
    file_id = None
    if os.path.exists(WELCOME_PHOTO_ID_FILE):
        with open(WELCOME_PHOTO_ID_FILE, "r") as f:
            file_id = f.read().strip()
    try:
        if file_id:
            await context.bot.send_photo(chat_id=user.id, photo=file_id, caption=caption_text)
        else:
            with open("Welcome_Image.png", "rb") as photo_file:
                sent_message = await context.bot.send_photo(chat_id=user.id, photo=photo_file, caption=caption_text)
            new_file_id = sent_message.photo[-1].file_id
            with open(WELCOME_PHOTO_ID_FILE, "w") as f:
                f.write(new_file_id)
    except Exception as e:
        logger.error(f"Error in start function: {e}")
        await update.message.reply_text(caption_text)

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (function is correct)
    admin_id = update.effective_user.id
    if admin_id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <your message>")
        return
    broadcast_text = " ".join(context.args)
    if not os.path.exists(USER_IDS_FILE):
        await update.message.reply_text("No users have started the bot yet.")
        return
    with open(USER_IDS_FILE, "r") as f:
        user_ids = [line.strip() for line in f]
    await update.message.reply_text(f"Starting broadcast to {len(user_ids)} users...")
    success_count, fail_count = 0, 0
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=broadcast_text)
            success_count += 1
        except (Forbidden, BadRequest):
            fail_count += 1
        await asyncio.sleep(0.1)
    await update.message.reply_text(f"Broadcast finished.\n\nSent: {success_count}\nFailed: {fail_count}")

async def forward_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (function is correct)
    user = update.effective_user
    save_user_id(user.id)
    await update.message.forward(chat_id=TELEGRAM_SUPPORT_CHAT_ID)
    reply_anchor = await context.bot.send_message(chat_id=TELEGRAM_SUPPORT_CHAT_ID, text=f"⬇️ Reply to this message to answer the user ⬇️\n(User ID: {user.id})")
    context.bot_data[str(reply_anchor.message_id)] = user.id
    confirmation_msg = await update.message.reply_text("Your message has been forwarded.")
    await asyncio.sleep(3)
    try:
        await context.bot.delete_message(chat_id=confirmation_msg.chat_id, message_id=confirmation_msg.message_id)
    except Exception as e:
        logger.warning(f"Could not delete confirmation message: {e}")

# --- THIS ENTIRE FUNCTION IS UPDATED ---
async def forward_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forwards a reply (all media types) from the support group to the user."""
    if not update.message or not update.message.reply_to_message:
        return

    replied_message_id = str(update.message.reply_to_message.message_id)
    user_id = context.bot_data.get(replied_message_id)

    if user_id:
        try:
            # Check for all common message types
            if update.message.text:
                await context.bot.send_message(chat_id=user_id, text=update.message.text)
            elif update.message.photo:
                await context.bot.send_photo(chat_id=user_id, photo=update.message.photo[-1].file_id, caption=update.message.caption)
            elif update.message.video:
                await context.bot.send_video(chat_id=user_id, video=update.message.video.file_id, caption=update.message.caption)
            elif update.message.sticker:
                await context.bot.send_sticker(chat_id=user_id, sticker=update.message.sticker.file_id)
            elif update.message.document:
                await context.bot.send_document(chat_id=user_id, document=update.message.document.file_id, caption=update.message.caption)
            else:
                await update.message.reply_text("Unsupported reply type.")
                return

            await update.message.reply_text("✅ Your reply has been sent.")
            del context.bot_data[replied_message_id]
        
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            await update.message.reply_text(f"❌ Failed to send message. Error: {e}")
    else:
        await update.message.reply_text("⚠️ **Error:** Could not find original user.")
