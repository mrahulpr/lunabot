import os
import importlib
import asyncio
import logging
from typing import Dict
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID", "-1001234567890")

# Log to file only (no console)
logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Load DB and error handler
from plugins import db
from plugins import stop_workflows

# Load text files
def load_text_file(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"*⚠️ Error loading `{filename}`:* ```{str(e)}```"

ABOUT_TEXT = load_text_file("about.txt")
HELP_HEADER = load_text_file("help.txt")
WELCOME_TEXT = load_text_file("welcome.txt")

# UI buttons
def build_main_menu_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("😜 About Me", callback_data="info"),
         InlineKeyboardButton("Help 🤗", callback_data="help")]
    ])

def build_help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])

def build_about_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="MarkdownV2",
        reply_markup=build_main_menu_markup()
    )

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        HELP_HEADER,
        parse_mode="MarkdownV2",
        reply_markup=build_help_keyboard()
    )

# Inline button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.edit_message_text(
            WELCOME_TEXT,
            parse_mode="MarkdownV2",
            reply_markup=build_main_menu_markup()
        )
    elif data == "info":
        await query.edit_message_text(
            ABOUT_TEXT,
            parse_mode="MarkdownV2",
            reply_markup=build_about_keyboard()
        )
    elif data == "help":
        await query.edit_message_text(
            HELP_HEADER,
            parse_mode="MarkdownV2",
            reply_markup=build_help_keyboard()
        )
    else:
        await query.edit_message_text(
            "❓ *Unknown selection\\.*",
            parse_mode="MarkdownV2",
            reply_markup=build_main_menu_markup()
        )

# Example cron job
async def my_cron_job(context: ContextTypes.DEFAULT_TYPE):
    logging.info("Cron job triggered.")

def setup_cron_job(app: Application):
    for job in app.job_queue.get_jobs_by_name("main_cron"):
        job.schedule_removal()
    app.job_queue.run_repeating(my_cron_job, interval=3600, first=60, name="main_cron")

# Auto-load plugins
async def load_plugins(app: Application):
    plugin_dir = "plugins"

    if not os.path.isdir(plugin_dir):
        await db.send_error_to_support("*⚠️ Plugins folder not found\\.*")
        return

    for file in os.listdir(plugin_dir):
        if file.endswith(".py") and file != "__init__.py":
            name = file[:-3]
            try:
                module = importlib.import_module(f"plugins.{name}")
                if hasattr(module, "setup"):
                    module.setup(app)
                    await db.send_log(f"*✅ Loaded plugin:* `{name}`")
                else:
                    await db.send_error_to_support(f"*⚠️ No `setup()` found in `{name}` plugin*")
            except Exception as e:
                await db.send_error_to_support(
                    f"*❌ Failed to load plugin `{name}`:* ```{str(e)}```"
                )

# Bot runner
async def run_bot():
    if not TOKEN:
        raise RuntimeError("❌ BOT_TOKEN is not set")

    # Build app first to use context
    app = ApplicationBuilder().token(TOKEN).build()

    await db.init_db()

    await load_plugins(app)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Notify support chat after restart
    async def notify_restart(context: ContextTypes.DEFAULT_TYPE):
        try:
            await context.bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text="✅ *Bot restarted successfully*",
                parse_mode="MarkdownV2"
            )
        except Exception as e:
            await db.send_error_to_support(f"*❌ Could not notify support chat\\:* ```{str(e)}```")

    app.job_queue.run_once(notify_restart, when=2)
    setup_cron_job(app)

    logging.info("🚀 Bot is running.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.wait()
    await app.stop()
    await app.shutdown()

# Entrypoint
if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except Exception as e:
        asyncio.run(db.send_error_to_support(f"*❌ Unhandled Exception\\:* ```{str(e)}```"))
