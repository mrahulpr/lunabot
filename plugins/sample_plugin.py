from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# Main command handler
async def sample_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Sample plugin is working!")

# Optional help callback handler for interactive help menu
async def sample_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="help")]]
    text = (
        "📘 *Sample Plugin*\n\n"
        "This is a basic structure to build your own plugin.\n\n"
        "*Usage:*\n"
        "`/sample` – Executes the sample command."
    )
    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard))

# Info metadata used for listing and help
def get_info():
    return {
        "name": "Sample Plugin 🧩",
        "description": "A simple example plugin structure you can reuse."
    }

# Register handlers with the bot
def setup(app):
    app.add_handler(CommandHandler("sample", sample_command))
    app.add_handler(CallbackQueryHandler(sample_help_callback, pattern="^plugin::sample$"))
