import os
import importlib
import traceback
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

app = ApplicationBuilder().token(TOKEN).build()

# Load plugins dynamically
for filename in os.listdir("plugins"):
    if filename.endswith(".py"):
        module_name = filename[:-3]
        module = importlib.import_module(f"plugins.{module_name}")
        for command in module.commands:
            app.add_handler(CommandHandler(command, module.handle))
        if hasattr(module, "callback"):
            app.add_handler(CallbackQueryHandler(module.callback))

async def start(update, context):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [[
        InlineKeyboardButton("ℹ️ Info", callback_data="info"),
        InlineKeyboardButton("❓ Help", callback_data="help")
    ]]
    await update.message.reply_text("👋 Welcome to the Bot!", reply_markup=InlineKeyboardMarkup(keyboard))

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
        print("Error in callback:")
        traceback.print_exc()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_start_callback, pattern="^(info|help)$"))

print("Bot running...")
app.run_polling()
