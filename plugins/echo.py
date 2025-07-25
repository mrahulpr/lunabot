from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler
)

# Format: {chat_id: set(user_ids)}
echo_db = {}

# Add echo
async def add_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a user to activate echo for them.")
    
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat_id
    echo_db.setdefault(chat_id, set()).add(user_id)
    await message.reply_text(f"✅ Echo activated for {user_id}.")

# Remove echo
async def rem_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to a user to deactivate echo.")
    
    user_id = message.reply_to_message.from_user.id
    chat_id = message.chat_id
    if chat_id in echo_db and user_id in echo_db[chat_id]:
        echo_db[chat_id].remove(user_id)
        await message.reply_text(f"❌ Echo deactivated for {user_id}.")
    else:
        await message.reply_text("ℹ️ Echo was not active for this user.")

# List active echoes
async def list_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in echo_db or not echo_db[chat_id]:
        return await update.message.reply_text("📝 Echo list is empty.")
    
    user_list = "\n".join([f"• `{uid}`" for uid in echo_db[chat_id]])
    await update.message.reply_text(f"👥 *Echo Active Users:*\n\n{user_list}", parse_mode="Markdown")

# Echo any message type
async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message: Message = update.message
    chat_id = message.chat_id
    sender_id = message.from_user.id

    if chat_id not in echo_db or sender_id not in echo_db[chat_id]:
        return

    # Echo all media types
    if message.text:
        await message.reply_text(message.text)
    elif message.photo:
        await message.reply_photo(message.photo[-1].file_id, caption=message.caption)
    elif message.video:
        await message.reply_video(message.video.file_id, caption=message.caption)
    elif message.document:
        await message.reply_document(message.document.file_id, caption=message.caption)
    elif message.sticker:
        await message.reply_sticker(message.sticker.file_id)
    elif message.audio:
        await message.reply_audio(message.audio.file_id, caption=message.caption)
    elif message.voice:
        await message.reply_voice(message.voice.file_id, caption=message.caption)
    elif message.animation:
        await message.reply_animation(message.animation.file_id, caption=message.caption)
    else:
        await message.reply_text("📎 Received an unsupported message type.")

# Help button
async def echo_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔁 *Echo Plugin*\n\n"
        "`/addecho` – Reply to a user to start echoing them.\n"
        "`/remecho` – Reply to stop echoing.\n"
        "`/listecho` – Show list of echoed users.\n\n"
        "Any message from the echoed user will be repeated by bot.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="help")]
        ])
    )

def get_info():
    return {
        "name": "Echo 🗣️",
        "description": "Repeat specific user's messages in chat."
    }

def setup(app):
    app.add_handler(CommandHandler("addecho", add_echo))
    app.add_handler(CommandHandler("remecho", rem_echo))
    app.add_handler(CommandHandler("listecho", list_echo))
    app.add_handler(CallbackQueryHandler(echo_help_callback, pattern=r"^plugin::echo$"))
    
    # Catch all messages for echoing
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), echo_handler))
