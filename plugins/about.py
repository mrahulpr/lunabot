from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# Updated info text with heading
INFO_TEXT = (
    "🧾 *About Me*\n\n"
    "👤 *Owner:* [Achhaaa 🙈](https://t.me/rahulp_r)\n"
    "👥 *Total Users:* അറിഞ്ഞിട്ട് എന്തിനാ 😂...\n"
    "🖥️ *Server:* Free Server Alla But Down ആയേക്കാം ⚡️\n"
    "🧠 *Memory:* 1 GB 😧\n"
    "📅 *Uptime:* Born on 29th Jan 👶\n"
    "🧾 *Bot Version:* v3.1.7 [Beta]"
)

# Responds to /about or /info
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await update.message.reply_text(INFO_TEXT, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# Handles button press for "ℹ️ Info"
async def info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await query.edit_message_text(INFO_TEXT, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

def setup(app):
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("info", about_command))
    app.add_handler(CallbackQueryHandler(info_callback, pattern="^info$"))

# No get_info(), so it won’t appear in Help
