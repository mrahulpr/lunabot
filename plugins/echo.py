from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# /echo command
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await update.message.reply_text(" ".join(context.args))
    else:
        await update.message.reply_text("❗ Usage: /echo <text>")

# Help view when user taps the plugin in the Help menu
async def echo_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🗣️ *Echo Plugin*\n\n"
        "Repeats back what you send.\n\n"
        "*Usage:* `/echo Hello`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="help")]]),
    )

def get_info():
    return {
        "name": "Echo 🗣️",
        "description": "Replies back with what you say."
    }

def setup(app):
    # /echo command
    app.add_handler(CommandHandler("echo", echo))
    # callback when clicking plugin button
    app.add_handler(CallbackQueryHandler(echo_help_callback, pattern=r"^plugin::echo$"))
