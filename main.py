import os import importlib import asyncio import logging from typing import Dict, Any from dotenv import load_dotenv from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup from telegram.ext import ( ApplicationBuilder, Application, CommandHandler, CallbackQueryHandler, ContextTypes, ) from plugins import stop_workflows from plugins.db import db  # <-- Required for error reporting

----------- Logging -----------

logging.basicConfig( filename="bot.log", format="%(asctime)s - %(message)s", level=logging.INFO )

----------- Load .env -----------

load_dotenv() TOKEN = os.getenv("BOT_TOKEN") SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID", "0")) PLUGINS: Dict[str, Dict[str, Any]] = {}

----------- Static Text Loaders -----------

def load_text_file(filename: str) -> str: try: with open(filename, 'r', encoding='utf-8') as f: return f.read() except Exception as e: return f"⚠️ Error loading {filename}: {e}"

ABOUT_TEXT = load_text_file("about.txt") HELP_HEADER = load_text_file("help.txt") WELCOME_TEXT = load_text_file("welcome.txt")

----------- Plugin Loader -----------

def load_plugins(app: Application) -> None: global PLUGINS PLUGINS.clear() plugin_dir = "plugins" if not os.path.isdir(plugin_dir): print("⚠️ No plugins folder found.") return

for file in os.listdir(plugin_dir):
    if file.endswith(".py") and file != "__init__.py":
        name = file[:-3]
        try:
            module = importlib.import_module(f"{plugin_dir}.{name}")
            if hasattr(module, "get_info"):
                PLUGINS[name] = module.get_info() or {}
            if hasattr(module, "setup"):
                module.setup(app)
            print(f"✅ Loaded plugin: {name}")
        except Exception as e:
            print(f"❌ Plugin load error [{name}]: {e}")
            try:
                asyncio.get_event_loop().run_until_complete(
                    db.send_error_to_support(f"*❌ Plugin `{name}` failed to load:* ```{str(e)}```")
                )
            except:
                pass

----------- UI Markups -----------

def build_main_menu_markup() -> InlineKeyboardMarkup: return InlineKeyboardMarkup([ [ InlineKeyboardButton("😜 About Me", callback_data="info"), InlineKeyboardButton("Help 🤗", callback_data="help"), ] ])

def build_help_keyboard() -> InlineKeyboardMarkup: return InlineKeyboardMarkup([ [InlineKeyboardButton("🔙 Back", callback_data="main_menu")] ])

def build_about_keyboard() -> InlineKeyboardMarkup: return InlineKeyboardMarkup([ [InlineKeyboardButton("🔙 Back", callback_data="main_menu")] ])

----------- Handlers -----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: await update.message.reply_text( WELCOME_TEXT, parse_mode="MarkdownV2", reply_markup=build_main_menu_markup() )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: await update.message.reply_text( HELP_HEADER, parse_mode="MarkdownV2", reply_markup=build_help_keyboard() )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: query = update.callback_query await query.answer() data = query.data

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
        "❓ Unknown selection.",
        reply_markup=build_main_menu_markup()
    )

----------- Cron Job Example -----------

async def my_cron_job(context: ContextTypes.DEFAULT_TYPE): print("🔁 Cron job executed.")

def setup_cron_job(app: Application): for old_job in app.job_queue.get_jobs_by_name("main_cron"): old_job.schedule_removal()

app.job_queue.run_repeating(
    my_cron_job,
    interval=60 * 60,
    first=120,
    name="main_cron"
)

----------- Startup -----------

def main(): if not TOKEN: raise RuntimeError("❌ BOT_TOKEN is not set.")

app = ApplicationBuilder().token(TOKEN).build()

try:
    load_plugins(app)
    stop_workflows.setup(app)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    async def notify_restart(context: ContextTypes.DEFAULT_TYPE):
        try:
            await context.bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text="✅ <b>Bot restarted successfully</b>",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"❌ Couldn't send restart message: {e}")

    app.job_queue.run_once(notify_restart, when=1)
    setup_cron_job(app)

    print("🚀 Bot is starting...")
    logging.info("🚀 Bot is running.")

    asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling()

except Exception as e:
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(db.send_error_to_support(f"*❌ Unhandled Exception:* ```{str(e)}```"))
    except Exception:
        pass
    raise

if name == "main": main()

