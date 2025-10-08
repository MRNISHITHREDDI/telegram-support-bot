import asyncio
import os
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import Forbidden, BadRequest
from settings import (
    TELEGRAM_SUPPORT_CHAT_ID,
    OWNER_ID
)
import logging

logger = logging.getLogger(__name__)
USER_IDS_FILE = "user_ids.txt"
WELCOME_PHOTO_ID_FILE = "welcome_photo_id.txt"
ADMIN_IDS_FILE = "admin_ids.txt"

# --- Admin Management Helper Functions ---
def load_admins() -> set:
    if not os.path.exists(ADMIN_IDS_FILE):
        with open(ADMIN_IDS_FILE, "w") as f:
            f.write(str(OWNER_ID) + "\n")
        return {str(OWNER_ID)}
    with open(ADMIN_IDS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_admins(admin_set: set):
    with open(ADMIN_IDS_FILE, "w") as f:
        for admin_id in sorted(admin_set, key=int):
            f.write(admin_id + "\n")

# --- States for Conversation (unchanged) ---
GETTING_MESSAGE, GETTING_BUTTONS, CONFIRM_BROADCAST = range(3)

# --- Standard Functions (unchanged) ---
def save_user_id(user_id: int):
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

# ... (forward_to_group and forward_to_user are unchanged)
async def forward_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def forward_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        return
    replied_message_id = str(update.message.reply_to_message.message_id)
    user_id = context.bot_data.get(replied_message_id)
    if user_id:
        try:
            await context.bot.send_message(chat_id=user_id, text=update.message.text)
            await update.message.reply_text("✅ Your reply has been sent.")
            del context.bot_data[replied_message_id]
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send message: {e}")
    else:
        await update.message.reply_text("⚠️ **Error:** Could not find original user.")


# --- UPDATED Admin Management Function ---
async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all current admins with their names and IDs."""
    if str(update.effective_user.id) not in load_admins():
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    admin_ids = load_admins()
    admin_list_parts = ["**Current Admins:**"]
    
    for admin_id in admin_ids:
        try:
            admin_chat = await context.bot.get_chat(chat_id=int(admin_id))
            display_name = admin_chat.first_name
            if admin_chat.last_name:
                display_name += f" {admin_chat.last_name}"
            admin_list_parts.append(f"• {display_name} (`{admin_id}`)")
        except Exception as e:
            logger.warning(f"Could not fetch info for admin ID {admin_id}: {e}")
            admin_list_parts.append(f"• Name not found (`{admin_id}`)")
    
    await update.message.reply_text("\n".join(admin_list_parts), parse_mode='Markdown')

# ... (add_admin and remove_admin are unchanged)
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only the bot owner can add new admins.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /addadmin <user_id>")
        return
    new_admin_id = context.args[0]
    admins = load_admins()
    if new_admin_id in admins:
        await update.message.reply_text(f"User `{new_admin_id}` is already an admin.", parse_mode='Markdown')
        return
    admins.add(new_admin_id)
    save_admins(admins)
    await update.message.reply_text(f"Successfully added `{new_admin_id}` as an admin.", parse_mode='Markdown')

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only the bot owner can remove admins.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /deladmin <user_id>")
        return
    admin_to_remove = context.args[0]
    if int(admin_to_remove) == OWNER_ID:
        await update.message.reply_text("You cannot remove the bot owner.")
        return
    admins = load_admins()
    if admin_to_remove not in admins:
        await update.message.reply_text(f"User `{admin_to_remove}` is not an admin.", parse_mode='Markdown')
        return
    admins.remove(admin_to_remove)
    save_admins(admins)
    await update.message.reply_text(f"Successfully removed `{admin_to_remove}` from admins.", parse_mode='Markdown')

# --- Broadcast Conversation Functions (unchanged) ---
# ... (All broadcast functions are the same as before)
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if str(update.effective_user.id) not in load_admins():
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END
    await update.message.reply_text("Please send the message you want to broadcast (text or photo with caption).\nType /cancel to stop.")
    return GETTING_MESSAGE
async def broadcast_get_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['broadcast_message'] = update.message
    await update.message.reply_text("Message received. Do you want to add inline buttons?\n\nIf yes, send them in the format:\n`Button Text - https://link.com`\n(One button per line)\n\nIf not, just type `no`.", parse_mode='Markdown')
    return GETTING_BUTTONS
async def broadcast_get_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    buttons_text = update.message.text
    broadcast_message = context.user_data['broadcast_message']
    keyboard = []
    if buttons_text.lower() != 'no':
        try:
            for line in buttons_text.split('\n'):
                if ' - ' in line:
                    text, url = line.split(' - ', 1)
                    keyboard.append([InlineKeyboardButton(text.strip(), url=url.strip())])
        except Exception as e:
            await update.message.reply_text(f"Error parsing buttons: {e}\nType /cancel to stop.")
            return GETTING_BUTTONS
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    context.user_data['reply_markup'] = reply_markup
    await update.message.reply_text("--- PREVIEW ---")
    if broadcast_message.text:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=broadcast_message.text, reply_markup=reply_markup)
    elif broadcast_message.photo:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=broadcast_message.photo[-1].file_id, caption=broadcast_message.caption, reply_markup=reply_markup)
    await update.message.reply_text("Type `yes` to send, or /cancel to stop.", parse_mode='Markdown')
    return CONFIRM_BROADCAST
async def broadcast_confirm_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() != 'yes':
        await update.message.reply_text("Broadcast cancelled.")
        return ConversationHandler.END
    broadcast_message = context.user_data['broadcast_message']
    reply_markup = context.user_data['reply_markup']
    if not os.path.exists(USER_IDS_FILE):
        await update.message.reply_text("No users found.")
        return ConversationHandler.END
    with open(USER_IDS_FILE, "r") as f:
        user_ids = [line.strip() for line in f]
    await update.message.reply_text(f"Broadcasting to {len(user_ids)} users...")
    success_count, fail_count = 0, 0
    for user_id in user_ids:
        try:
            if broadcast_message.text:
                await context.bot.send_message(chat_id=user_id, text=broadcast_message.text, reply_markup=reply_markup)
            elif broadcast_message.photo:
                await context.bot.send_photo(chat_id=user_id, photo=broadcast_message.photo[-1].file_id, caption=broadcast_message.caption, reply_markup=reply_markup)
            success_count += 1
        except (Forbidden, BadRequest):
            fail_count += 1
        await asyncio.sleep(0.1)
    await update.message.reply_text(f"Broadcast finished!\n\nSent: {success_count}\nFailed: {fail_count}")
    context.user_data.clear()
    return ConversationHandler.END
async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Broadcast cancelled.")
    context.user_data.clear()
    return ConversationHandler.END
