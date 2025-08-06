import os
import importlib
import asyncio
import logging
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
from plugins.db import db, send_log, send_error_to_support  # for error reporting

# ----------- Logging -----------
logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s - %(message)s",
    level=logging.INFO
)

# ----------- Load .env -----------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID=os.getenv("SUPPORT_CHAT_ID")


PLUGINS: Dict[str, Dict[str, Any]] = {}

# ----------- Static Text Loaders -----------
def load_text_file(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"⚠️ Error loading {filename}: {e}"

ABOUT_TEXT = load_text_file("about.txt")
HELP_HEADER = load_text_file("help.txt")
WELCOME_TEXT = load_text_file("welcome.txt")

# ----------- Async Plugin Loader -----------
async def load_plugins(app: Application) -> None:
    global PLUGINS
    PLUGINS.clear()
    plugin_dir = "plugins"
    if not os.path.isdir(plugin_dir):
        return

    import traceback

    for file in os.listdir(plugin_dir):
        if file.endswith(".py") and file != "__init__.py":
            name = file[:-3]
            try:
                module = importlib.import_module(f"{plugin_dir}.{name}")

                if hasattr(module, "setup"):
                    module.setup(app)

                if hasattr(module, "test"):
                    try:
                        await module.test()
                        await send_log(f"✅ *Plugin loaded:* `{name}`")
                    except Exception as test_err:
                        await send_error_to_support(
                            f"*❌ Plugin `{name}` test failed:*\n`{test_err}`\n```{traceback.format_exc()}```"
                        )
                        continue

                if hasattr(module, "get_info"):
                    PLUGINS[name] = module.get_info() or {}

            except Exception as e:
                await send_error_to_support(
                    f"*❌ Plugin `{name}` load error:*\n`{e}`\n```{traceback.format_exc()}```"
                )

# ----------- UI Markups -----------
def build_main_menu_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("😜 About Me", callback_data="info"),
            InlineKeyboardButton("Help 🤗", callback_data="help"),
        ]
    ])

def build_help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])

def build_about_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])

# ----------- Handlers -----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="MarkdownV2",
        reply_markup=build_main_menu_markup(),
        disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        HELP_HEADER,
        parse_mode="MarkdownV2",
        reply_markup=build_help_keyboard(),
        disable_web_page_preview=True
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.edit_message_text(
            WELCOME_TEXT,
            parse_mode="MarkdownV2",
            reply_markup=build_main_menu_markup(),
            disable_web_page_preview=True
        )
    elif data == "info":
        await query.edit_message_text(
            ABOUT_TEXT,
            parse_mode="MarkdownV2",
            reply_markup=build_about_keyboard(),
            disable_web_page_preview=True
        )
    elif data == "help":
        await query.edit_message_text(
            HELP_HEADER,
            parse_mode="MarkdownV2",
            reply_markup=build_help_keyboard(),
            disable_web_page_preview=True
        )
    else:
        # Unknown callback — IGNORE to let plugin handlers deal with it
        return



# ----------- Main Function -----------
def main():
    if not TOKEN:
        raise RuntimeError("❌ BOT_TOKEN is not set.")

    app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(info|help|main_menu)$"))  # general button handler




async def startup_tasks(context: ContextTypes.DEFAULT_TYPE):
    await load_plugins(app)
    await context.bot.send_message(
        chat_id=SUPPORT_CHAT_ID,
        text="✅ <b>Bot restarted successfully</b>",
        parse_mode="HTML"
    )

    app.job_queue.run_once(startup_tasks, when=1)

    print("🚀 Bot is starting...")
    logging.info("🚀 Bot is running.")
    app.run_polling()

if __name__ == "__main__":
    main()
