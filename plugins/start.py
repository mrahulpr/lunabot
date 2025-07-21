from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler

FEATURES = {
    "echo": "Echoes back your message",
    "notify": "Sends restart notification",
}

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [InlineKeyboardButton("❓ Help", callback_data="help_menu")]
    ]
    update.message.reply_text("👋 Welcome to your bot!", reply_markup=InlineKeyboardMarkup(keyboard))

def info_cb(update: Update, context: CallbackContext):
    update.callback_query.answer()
    update.callback_query.edit_message_text("ℹ️ Personal modular bot.")

def help_cb(update: Update, context: CallbackContext):
    update.callback_query.answer()
    buttons = [
        [InlineKeyboardButton(f"{k.title()}", callback_data=f"feature_{k}")]
        for k in FEATURES
    ] + [[InlineKeyboardButton("⬅️ Back", callback_data="start_again")]]
    update.callback_query.edit_message_text("🔍 Choose a feature:", reply_markup=InlineKeyboardMarkup(buttons))

def feature_cb(update: Update, context: CallbackContext):
    k = update.callback_query.data.replace("feature_", "")
    update.callback_query.answer()
    update.callback_query.edit_message_text(f"🧩 *{k.title()}*\n\n{FEATURES[k]}", parse_mode="Markdown")

def back_cb(update: Update, context: CallbackContext):
    update.callback_query.answer()
    start(update.callback_query, context)

def register(dispatcher, bot):
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(info_cb, pattern="^info$"))
    dispatcher.add_handler(CallbackQueryHandler(help_cb, pattern="^help_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(feature_cb, pattern="^feature_"))
    dispatcher.add_handler(CallbackQueryHandler(back_cb, pattern="^start_again$"))
