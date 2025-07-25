from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Set to store chat_ids where echo is active
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
    await update.message.reply_text("✅ Echo mode activated. All messages will be echoed back.")

# /deleteecho command
async def delete_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in echo_enabled_chats:
        echo_enabled_chats.remove(chat_id)
        await update.message.reply_text("❌ Echo mode deactivated.")
    else:
        await update.message.reply_text("⚠️ Echo mode was not active.")

# Handler for all messages (after addecho)
async def auto_echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in echo_enabled_chats and update.message.text:
        await update.message.reply_text(update.message.text)

# Help view when user taps the plugin in the Help menu
async def echo_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🗣️ *Echo Plugin*\n\n"
        "1. `/echo Hello` – Replies with 'Hello'.\n"
        "2. `/addecho` – Starts echoing all messages in this chat.\n"
        "3. `/deleteecho` – Stops echoing messages.\n\n"
        "_Useful for testing or fun interactions._",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="help")]
        ]),
    )

# Info for Help menu
def get_info():
    return {
        "name": "Echo 🗣️",
        "description": "Replies back with what you say. Now with full chat echo!"
    }

# Setup the plugin
def setup(app):
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("addecho", add_echo))
    app.add_handler(CommandHandler("deleteecho", delete_echo))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_echo))
    app.add_handler(CallbackQueryHandler(echo_help_callback, pattern=r"^plugin::echo$"))
