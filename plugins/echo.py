from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Track chats where echo is active
echo_enabled_chats = set()

# /echo command
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await update.message.reply_text(" ".join(context.args))
    else:
        await update.message.reply_text("❗ Usage: /echo <text>")

# /addecho command
async def add_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    echo_enabled_chats.add(chat_id)
    await update.message.reply_text("✅ Echo mode activated. I will now echo everything!")

# /deleteecho command
async def delete_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in echo_enabled_chats:
        echo_enabled_chats.remove(chat_id)
        await update.message.reply_text("❌ Echo mode deactivated.")
    else:
        await update.message.reply_text("⚠️ Echo mode was not active.")

# Echo all message types
async def auto_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message

    if chat_id not in echo_enabled_chats or not message:
        return

    if message.text:
        await message.reply_text(message.text)

    elif message.photo:
        await message.reply_photo(photo=message.photo[-1].file_id, caption=message.caption or "")

    elif message.video:
        await message.reply_video(video=message.video.file_id, caption=message.caption or "")

    elif message.document:
        await message.reply_document(document=message.document.file_id, caption=message.caption or "")

    elif message.sticker:
        await message.reply_sticker(sticker=message.sticker.file_id)

    elif message.voice:
        await message.reply_voice(voice=message.voice.file_id, caption=message.caption or "")

    elif message.audio:
        await message.reply_audio(audio=message.audio.file_id, caption=message.caption or "")

    elif message.animation:
        await message.reply_animation(animation=message.animation.file_id, caption=message.caption or "")

    else:
        await message.reply_text("⚠️ Unsupported message type.")

# Help for the Help menu
async def echo_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🗣️ *Echo Plugin*\n\n"
        "`/echo Hello` – Replies with 'Hello'.\n"
        "`/addecho` – Activates full echo mode in this chat.\n"
        "`/deleteecho` – Deactivates echo mode.\n\n"
        "⚙️ All types (text, image, video, etc.) will be echoed.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="help")]
        ]),
    )

# Help info block
def get_info():
    return {
        "name": "Echo 🗣️",
        "description": "Echoes all message types in chats. Great for testing or fun."
    }

# Register handlers
def setup(app):
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("addecho", add_echo))
    app.add_handler(CommandHandler("deleteecho", delete_echo))
    app.add_handler(MessageHandler(filters.ALL, auto_echo))  # <-- now captures all message types
    app.add_handler(CallbackQueryHandler(echo_help_callback, pattern=r"^plugin::echo$"))
