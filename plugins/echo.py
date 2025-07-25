from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Track active echo chats
echo_enabled_chats = set()

# /echo command (manual trigger)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await update.message.reply_text(" ".join(context.args))
    else:
        await update.message.reply_text("❗ Usage: /echo <text>")

# /addecho command
async def add_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    echo_enabled_chats.add(chat_id)
    await update.message.reply_text("✅ Echo mode activated. I will echo every message sent in this chat.")

# /deleteecho command
async def delete_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in echo_enabled_chats:
        echo_enabled_chats.remove(chat_id)
        await update.message.reply_text("❌ Echo mode deactivated.")
    else:
        await update.message.reply_text("⚠️ Echo mode was not active.")

# Handle ALL incoming messages and media
async def auto_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.effective_message  # <-- This captures all, not just .message

    if chat_id not in echo_enabled_chats:
        return

    if message.text:
        await message.reply_text(message.text)

    elif message.photo:
        await message.reply_photo(message.photo[-1].file_id, caption=message.caption or "")

    elif message.video:
        await message.reply_video(message.video.file_id, caption=message.caption or "")

    elif message.document:
        await message.reply_document(message.document.file_id, caption=message.caption or "")

    elif message.sticker:
        await message.reply_sticker(message.sticker.file_id)

    elif message.voice:
        await message.reply_voice(message.voice.file_id, caption=message.caption or "")

    elif message.audio:
        await message.reply_audio(message.audio.file_id, caption=message.caption or "")

    elif message.animation:
        await message.reply_animation(message.animation.file_id, caption=message.caption or "")

    else:
        await message.reply_text("⚠️ Unsupported message type received.")

# Help handler
async def echo_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "🗣️ *Echo Plugin Help*\n\n"
        "`/echo Hello` – Replies with 'Hello'.\n"
        "`/addecho` – Activates echo mode in this chat.\n"
        "`/deleteecho` – Stops echoing.\n\n"
        "✨ Echoes ALL message types (text, media, stickers, etc.)",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="help")]
        ]),
    )

# Plugin metadata
def get_info():
    return {
        "name": "Echo 🗣️",
        "description": "Echoes all messages in enabled chats, including media."
    }

# Plugin setup
def setup(app):
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("addecho", add_echo))
    app.add_handler(CommandHandler("deleteecho", delete_echo))
    app.add_handler(MessageHandler(filters.ALL, auto_echo))  # Important: listen to all!
    app.add_handler(CallbackQueryHandler(echo_help_callback, pattern=r"^plugin::echo$"))
