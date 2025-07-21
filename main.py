import os
import importlib
import traceback
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

app = ApplicationBuilder().token(TOKEN).build()

# Load plugins from 'plugins' folder
try:
    for filename in os.listdir("plugins"):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = filename[:-3]
            module = importlib.import_module(f"plugins.{module_name}")
            for command in module.commands:
                app.add_handler(CommandHandler(command, module.handle))
            if hasattr(module, "callback"):
                app.add_handler(CallbackQueryHandler(module.callback))
except Exception as e:
    print("❌ Error loading plugins:")
    traceback.print_exc()

# /start command handler
async def start(update, context):
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[
            InlineKeyboardButton("ℹ️ Info", callback_data="info"),
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]]
        await update.message.reply_text(
            "👋 Welcome to the Bot!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print("❌ Error in /start command:")
        traceback.print_exc()

# Button callback handler
async def handle_start_callback(update, context):
    try:
        query = update.callback_query
        await query.answer()
        if query.data == "info":
            await query.edit_message_text("ℹ️ This is your personal assistant bot.")
        elif query.data == "help":
            await query.edit_message_text(
                """Here are the features:

/restart - Restart bot (owner only)
/echo - Repeat your message
/calc - Open calculator with buttons"""
            )
    except Exception as e:
        print("❌ Error in callback handler:")
        traceback.print_exc()

# Register handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_start_callback, pattern="^(info|help)$"))

print("✅ Bot running...")
try:
    app.run_polling()
except Exception as e:
    print("❌ Bot crashed during polling:")
    traceback.print_exc()
