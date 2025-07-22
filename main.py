import os
import importlib
import asyncio
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    Application
)
import logging

# --- Config ---
TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = -1002379666380  # ✅ Replace with your log channel ID

# --- Logging Setup ---
logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- Plugin Registry ---
PLUGINS: Dict[str, Dict[str, Any]] = {}

# --- Load Plugins ---
def load_plugins(app: Application):
    plugins_path = os.path.join(os.path.dirname(__file__), "plugins")
    for filename in os.listdir(plugins_path):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f"plugins.{module_name}")
                if hasattr(module, "get_info") and hasattr(module, "setup"):
                    info = module.get_info()
                    module.setup(app)
                    PLUGINS[info["name"]] = {
                        "module": module,
                        "info": info,
                    }
                    logging.info(f"✅ Loaded plugin: {info['name']}")
                else:
                    logging.warning(f"⚠️ Plugin '{module_name}' missing get_info() or setup()")
            except Exception as e:
                logging.error(f"❌ Failed to load plugin {module_name}: {e}")

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome = (
        "<b>👋 ഹായ്<br>Bot-ലേക്ക് സ്വാഗതം!</b>\n"
        "<b>എന്തും Special ഇല്ല ഇവിടെ.</b>\n"
        "<a href='https://t.me/rahulp_r'>എൻ്റെ അച്ഛൻ 😇</a> എന്നെ വെറുതെ ഉണ്ടാക്കിയതാണ്."
    )
    buttons = [
        [
            InlineKeyboardButton("ℹ️ Info", callback_data="info"),
            InlineKeyboardButton("🆘 Help", callback_data="help")
        ]
    ]
    await update.message.reply_html(welcome, reply_markup=InlineKeyboardMarkup(buttons))

# --- Help Command ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_plugins_menu(update.message, context)

# --- Show Plugins Menu ---
async def show_plugins_menu(target, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(info["info"]["name"], callback_data=f"plugin_{name}")]
        for name, info in PLUGINS.items()
    ]
    if keyboard:
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await target.reply_text("📚 Available Plugins:", reply_markup=reply_markup)

# --- Callback Handler ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "help":
        await show_plugins_menu(query.message, context)
    elif data == "info":
        await query.edit_message_text(
            "<b>🤖 About Me</b>\n"
            "Owner: Achhaaa 🙈 [@rahulp_r](https://t.me/rahulp_r)\n"
            "Total Users: അറിയണ്ടത് എന്തിനാ 😂...\n"
            "Server: Free Server അല്ല, പക്ഷേ Down ആവും ⚡️\n"
            "Memory: 1 GB 😧\n"
            "Uptime: Born on 29th Jan 👶\n"
            "Version: v3.1.7 [Beta]",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    elif data == "back_to_main":
        await start(update, context)
    elif data.startswith("plugin_"):
        plugin_name = data.replace("plugin_", "")
        plugin = PLUGINS.get(plugin_name, {}).get("module")
        if plugin and hasattr(plugin, "run"):
            await plugin.run(update, context)
        else:
            await query.edit_message_text("⚠️ Plugin not found or missing run().")

# --- Notify log channel ---
async def notify_log_channel(bot):
    try:
        await bot.send_message(
            chat_id=LOG_CHANNEL_ID,
            text="✅ Bot has started and is now live!"
        )
    except Exception as e:
        logging.error(f"❌ Failed to send startup log: {e}")

# --- Main ---
def main() -> None:
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN not set in environment.")
    
    app = ApplicationBuilder().token(TOKEN).build()

    load_plugins(app)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    logging.info("🚀 Bot is starting...")

    async def run():
        await notify_log_channel(app.bot)
        await app.run_polling()

    asyncio.run(run())

if __name__ == "__main__":
    main()
