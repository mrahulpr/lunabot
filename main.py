import os
import importlib
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    Application,
)

# Load env variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")

# Logging to file
logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Import DB and error handler
from plugins import db

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

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="MarkdownV2",
        reply_markup=build_main_menu_markup()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        HELP_HEADER,
        parse_mode="MarkdownV2",
        reply_markup=build_help_keyboard()
    )

# Inline buttons
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

# Load all plugins
async def load_plugins(app: Application):
    plugin_dir = "plugins"
    if not os.path.isdir(plugin_dir):
        await db.send_error_to_support("*⚠️ Plugins folder not found\\.*")
        return

    for file in os.listdir(plugin_dir):
        if file.endswith(".py") and file not in ["__init__.py", "db.py"]:
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
                    f"*❌ Plugin `{name}` failed to load:* ```{str(e)}```"
                )

# Main bot runner
async def run_bot():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = ApplicationBuilder().token(TOKEN).build()
    await db.init_db()
    await load_plugins(app)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    async def notify_restart(context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text="✅ *Bot restarted successfully*",
            parse_mode="MarkdownV2"
        )

    app.job_queue.run_once(notify_restart, when=2)
    setup_cron_job(app)

    logging.info("🚀 Bot polling started.")
    await app.run_polling()

# Entrypoint
if __name__ == "__main__":
    async def main():
        try:
            await run_bot()
        except Exception as e:
            await db.send_error_to_support(f"*❌ Unhandled Exception:* ```{str(e)}```")

    asyncio.get_event_loop().run_until_complete(main())
