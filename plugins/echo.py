from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# /echo command
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await update.message.reply_text(" ".join(context.args))
    else:
        await update.message.reply_text("❗ Usage: /echo <text>")

# Button callback for plugin::echo
async def echo_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="help")]]
    text = (
        "🗣️ *Echo Plugin*\n\n"
        "This plugin repeats back whatever you send.\n\n"
        "*Usage:*\n"
        "`/echo Hello there!` → replies with 'Hello there!'\n"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# Info for Help menu
def get_info():
    return {
        "name": "Echo 🗣️",
        "description": "Replies back with what you say."
    }

# Register handlers
def setup(app):
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CallbackQueryHandler(echo_help_callback, pattern="^plugin::echo$"))
