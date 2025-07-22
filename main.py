import os
import importlib
from typing import Dict, Any
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import logging

logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s - %(message)s",
    level=logging.INFO
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
PLUGINS: Dict[str, Dict[str, Any]] = {}

# ------------------------
# Plugin loading
# ------------------------
def load_plugins(app: Application) -> None:
    global PLUGINS
    PLUGINS.clear()
    plugin_dir = "plugins"

    if not os.path.isdir(plugin_dir):
        print("⚠️ No plugins/ directory found.")
        return

    for file in os.listdir(plugin_dir):
        if not file.endswith(".py") or file == "__init__.py":
            continue
        name = file[:-3]
        try:
            module = importlib.import_module(f"{plugin_dir}.{name}")
            if hasattr(module, "get_info"):
                info = module.get_info() or {}
                PLUGINS[name] = info
            if hasattr(module, "setup"):
                module.setup(app)
            print(f"✅ Loaded plugin: {name}")
        except Exception as e:
            print(f"❌ Failed to load plugin {name}: {e}")

# ------------------------
# UI builders
# ------------------------
def build_main_menu_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("😜 About Me", callback_data="info"),
                InlineKeyboardButton("Help 🤗", callback_data="help"),
            ]
        ]
    )

def build_help_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(info["name"], callback_data=f"plugin::{key}")]
        for key, info in PLUGINS.items()
    ]
    if not rows:
        rows = [[InlineKeyboardButton("⛔ No plugins available", callback_data="none")]]
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)

# ------------------------
# Handlers
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '<b>👋 Hi\nWelcome to the Bot, Nothing special Here.</b> '
        '<a href="https://t.me/rahulp_r">എൻ്റെ അച്ഛൻ 😇</a> എന്നെ വെറുതെ ഉണ്ടാക്കിയതാണ്.',
        parse_mode="HTML",
        reply_markup=build_main_menu_markup()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🧩 Available Plugins:",
        reply_markup=build_help_keyboard(),
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.message.reply_text(
            '<b>👋 Hi\nWelcome to the Bot, Nothing special Here.</b> '
            '<a href="https://t.me/rahulp_r">എൻ്റെ അച്ഛൻ 😇</a> എന്നെ വെറുതെ ഉണ്ടാക്കിയതാണ്.',
            parse_mode="HTML",
            reply_markup=build_main_menu_markup()
        )

    elif data == "info":
        await query.edit_message_text(
            "ℹ️ This bot auto-loads plugins and runs on GitHub Actions.",
            reply_markup=build_main_menu_markup(),
        )

    elif data == "help":
        await query.edit_message_text(
            "**അധികം Modules ഇല്ലാത്തതിനാൽ ക്ഷമിക്കണം അച്ഛൻ തിരക്കിൽ ആയിരുന്നു 😅. He will add More in Future 👍**",
            reply_markup=build_help_keyboard(),
        )

    elif data.startswith("plugin::"):
        plugin_key = data.split("plugin::", 1)[1]
        plugin_info = PLUGINS.get(plugin_key, {})
        desc = plugin_info.get("description", "No description available.")
        await query.edit_message_text(
            desc,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="help")]]
            ),
        )

    else:
        await query.edit_message_text(
            "❓ Unknown selection.",
            reply_markup=build_main_menu_markup(),
        )

# ------------------------
# Main entry
# ------------------------
def main() -> None:
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN not set in environment.")

    app = ApplicationBuilder().token(TOKEN).build()
    load_plugins(app)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Bot starting...")
    logging.info("🚀 Bot started and logging enabled.")
    app.run_polling()

if __name__ == "__main__":
    main()
