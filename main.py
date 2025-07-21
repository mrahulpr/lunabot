import os
import importlib
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

PLUGINS = {}

def load_plugins(app):
    global PLUGINS
    PLUGINS.clear()
    plugin_dir = "plugins"

    for file in os.listdir(plugin_dir):
        if file.endswith(".py") and file != "__init__.py":
            name = file[:-3]
            module = importlib.import_module(f"{plugin_dir}.{name}")
            if hasattr(module, "get_info"):
                PLUGINS[name] = module.get_info()

            # 🔌 Optional plugin setup(app)
            if hasattr(module, "setup"):
                module.setup(app)

def build_help_keyboard():
    keyboard = [
        [InlineKeyboardButton(f"🔹 {info['name']}", callback_data=f"plugin_{key}")]
        for key, info in PLUGINS.items()
    ]
    if not keyboard:
        keyboard = [[InlineKeyboardButton("⛔ No plugins available", callback_data="none")]]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("ℹ️ Info", callback_data="info"),
            InlineKeyboardButton("🆘 Help", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Welcome! I am your modular Telegram bot.", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await start(update, context)
    elif data == "info":
        await query.edit_message_text("ℹ️ This bot is designed to auto-load plugins and run 24/7 via GitHub Actions.")
    elif data == "help":
        await query.edit_message_text("🧩 Available Plugins:", reply_markup=build_help_keyboard())
    elif data.startswith("plugin_"):
        plugin_key = data.split("_", 1)[1]
        plugin_info = PLUGINS.get(plugin_key, {})
        text = plugin_info.get("description", "No description available.")
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="help")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text("❓ Unknown command.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    load_plugins(app)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
