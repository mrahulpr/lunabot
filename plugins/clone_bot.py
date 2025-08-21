"""
Clone Bot Plugin for LunaBot
Allows users to create their own bot instances using their bot tokens
"""

import os
import asyncio
import traceback
import subprocess
import tempfile
import shutil
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from .db import db, send_log, send_error_to_support

# Collection for storing clone bot data
clone_bots_collection = db["clone_bots"]

class CloneBotManager:
    def __init__(self):
        self.running_bots = {}  # Store running bot processes
        
    async def create_clone_bot(self, user_id: int, bot_token: str, user_name: str) -> dict:
        """
        Create a clone bot instance for a user
        """
        user_id = update.effective_user.id
        try:
            # Validate the bot token by creating a Bot instance
            test_bot = Bot(token=bot_token)
            bot_info = await test_bot.get_me()
            
            # Store clone bot information in database
            clone_data = {
                "user_id": user_id,
                "user_name": user_name,
                "bot_token": bot_token,
                "bot_username": bot_info.username,
                "bot_id": bot_info.id,
                "created_at": datetime.utcnow(),
                "status": "active",
                "error_count": 0
            }
            
            # Check if user already has a clone bot
            existing_clone = await clone_bots_collection.find_one({"user_id": user_id})
            if existing_clone:
                # Update existing clone
                await clone_bots_collection.update_one(
                    {"user_id": user_id},
                    {"$set": clone_data}
                )
            else:
                # Insert new clone
                await clone_bots_collection.insert_one(clone_data)
            
            # Create bot directory
            bot_dir = f"/tmp/clone_bot_{user_id}"
            if os.path.exists(bot_dir):
                shutil.rmtree(bot_dir)
            os.makedirs(bot_dir)
            
            # --- START OF CORRECTION ---
            # Dynamically determine the source directory based on this script's location
            # This makes the path relative and portable, fixing the "No such file" error.
            script_dir = os.path.dirname(os.path.abspath(__file__))
            source_dir = os.path.abspath(os.path.join(script_dir, '..')) # Assumes this plugin is in a 'plugins' folder
            # --- END OF CORRECTION ---
            
            # Copy main bot files to clone directory
            shutil.copy2(f"{source_dir}/main.py", bot_dir)
            shutil.copy2(f"{source_dir}/requirements.txt", bot_dir)
            shutil.copy2(f"{source_dir}/about.txt", bot_dir)
            shutil.copy2(f"{source_dir}/help.txt", bot_dir)
            shutil.copy2(f"{source_dir}/welcome.txt", bot_dir)
            
            # Copy plugins directory
            shutil.copytree(f"{source_dir}/plugins", f"{bot_dir}/plugins")
            
            # Create .env file for clone bot
            env_content = f"""BOT_TOKEN={bot_token}
MONGO_URI={os.getenv('MONGO_URI')}
SUPPORT_CHAT_ID={os.getenv('SUPPORT_CHAT_ID')}
OWNER_ID={os.getenv('OWNER_ID')}
CLONE_OWNER_ID={user_id}
"""
            with open(f"{bot_dir}/.env", "w") as f:
                f.write(env_content)
            
            # Create a modified main.py that reports errors to main support
            await self._create_clone_main_py(bot_dir, user_id, bot_info.username)
            
            return {
                "success": True,
                "bot_username": bot_info.username,
                "bot_id": bot_info.id,
                "message": f"✅ Clone bot @{bot_info.username} created successfully!"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ Failed to create clone bot: {str(e)}"
            }
    
    async def _create_clone_main_py(self, bot_dir: str, owner_id: int, bot_username: str):
        """
        Create a modified main.py for clone bots that reports errors to main support
        """
        main_py_content = f'''import os
import importlib
import asyncio
import logging
import traceback
from typing import Dict, Any
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ----------- Logging -----------
logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s - %(message)s",
    level=logging.INFO
)

# ----------- Load .env -----------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")
CLONE_OWNER_ID = {owner_id}

# Error reporting bot (main bot)
error_bot = Bot(token=os.getenv("MAIN_BOT_TOKEN", TOKEN))

async def send_clone_error_to_support(text: str):
    """Send clone bot errors to main support chat"""
    try:
        error_message = f"🤖 *Clone Bot Error (@{bot_username})*\\n"
        error_message += f"*Owner:* `{CLONE_OWNER_ID}`\\n\\n"
        error_message += text
        
        await error_bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=error_message[:4000],
            parse_mode="MarkdownV2"
        )
    except Exception:
        pass

PLUGINS: Dict[str, Dict[str, Any]] = {{}}

# ----------- Static Text Loaders -----------
def load_text_file(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"⚠️ Error loading {{filename}}: {{e}}"

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

    for file in os.listdir(plugin_dir):
        if file.endswith(".py") and file != "__init__.py":
            name = file[:-3]
            try:
                module = importlib.import_module(f"{{plugin_dir}}.{{name}}")

                if hasattr(module, "setup"):
                    module.setup(app)

                if hasattr(module, "test"):
                    try:
                        await module.test()
                    except Exception as test_err:
                        await send_clone_error_to_support(
                            f"*❌ Plugin `{{name}}` test failed:*\\n`{{test_err}}`\\n```{{traceback.format_exc()}}```"
                        )
                        continue

                if hasattr(module, "get_info"):
                    PLUGINS[name] = module.get_info() or {{}}

            except Exception as e:
                await send_clone_error_to_support(
                    f"*❌ Plugin `{{name}}` load error:*\\n`{{e}}`\\n```{{traceback.format_exc()}}```"
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
        return

# ----------- Error Handler -----------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and send to support"""
    try:
        error_text = f"*❌ Clone Bot Error:*\\n`{{str(context.error)}}`\\n```{{traceback.format_exc()}}```"
        await send_clone_error_to_support(error_text)
    except Exception:
        pass

# ----------- Main Function -----------
def main():
    if not TOKEN:
        raise RuntimeError("❌ BOT_TOKEN is not set.")

    application = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()

    # Add error handler
    application.add_error_handler(error_handler)

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(info|help|main_menu)$"))

    async def post_init(app: Application):
        await load_plugins(app)
        try:
            await send_clone_error_to_support(f"✅ *Clone bot @{bot_username} started successfully*")
        except Exception:
            pass

    # Set post-init tasks
    application.post_init = post_init

    print("🚀 Clone Bot is starting...")
    logging.info("🚀 Clone Bot is running.")
    application.run_polling()

if __name__ == "__main__":
    main()
'''
        
        with open(f"{bot_dir}/main.py", "w") as f:
            f.write(main_py_content)

# Global clone bot manager instance
clone_manager = CloneBotManager()

async def clone_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /clonebot command
    """
    try:
        user = update.effective_user
        
        if not context.args:
            help_text = """🤖 *Clone Bot Creator*

To create your own bot instance, use:
`/clonebot YOUR_BOT_TOKEN`

*How to get a bot token:*
1\\. Message @BotFather on Telegram
2\\. Send `/newbot`
3\\. Follow the instructions to create your bot
4\\. Copy the token and use it with this command

*Example:*
`/clonebot 123456789:ABCdefGHIjklMNOpqrSTUvwxyz`

⚠️ *Important:*
• Keep your token private
• Your clone bot will have the same features as this bot
• All errors will be reported to our support team
• You can update your clone bot by running the command again"""

            await update.message.reply_text(help_text, parse_mode="MarkdownV2")
            return
        
        bot_token = context.args[0].strip()
        
        # Validate token format
        if not bot_token or ":" not in bot_token:
            await update.message.reply_text(
                "❌ Invalid token format. Please provide a valid bot token from @BotFather."
            )
            return
        
        # Show processing message
        processing_msg = await update.message.reply_text("🔄 Creating your clone bot... Please wait.")
        
        # Create clone bot
        result = await clone_manager.create_clone_bot(
            user_id=user.id,
            bot_token=bot_token,
            user_name=user.first_name or user.username or str(user.id)
        )
        
        if result["success"]:
            success_text = f"""✅ *Clone Bot Created Successfully!*

🤖 *Bot Username:* @{result['bot_username']}
🆔 *Bot ID:* `{result['bot_id']}`

Your bot is now ready to use! You can:
• Add it to groups
• Use all the same commands as this bot
• Customize it further if needed

*Note:* Your bot will start automatically. All errors and logs will be forwarded to our support team for monitoring."""

            await processing_msg.edit_text(success_text, parse_mode="MarkdownV2")
            
            # Log to support
            await send_log(
                f"🤖 *New Clone Bot Created*\\n"
                f"• *Owner:* {user.first_name or 'N/A'} \\(@{user.username or 'N/A'}\\)\\n"
                f"• *Owner ID:* `{user.id}`\\n"
                f"• *Bot:* @{result['bot_username']}\\n"
                f"• *Bot ID:* `{result['bot_id']}`"
            )
            
        else:
            await processing_msg.edit_text(result["message"])
            
            # Log error to support
            await send_error_to_support(
                f"*❌ Clone Bot Creation Failed*\\n"
                f"• *User:* {user.first_name or 'N/A'} \\(@{user.username or 'N/A'}\\)\\n"
                f"• *User ID:* `{user.id}`\\n"
                f"• *Error:* `{result.get('error', 'Unknown error')}`"
            )
            
    except Exception as e:
        await send_error_to_support(
            f"*❌ Clone Bot Command Error:*\\n`{str(e)}`\\n```{traceback.format_exc()}```"
        )
        await update.message.reply_text("❌ An error occurred while creating your clone bot. Please try again later.")

async def list_clone_bots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    List all clone bots (admin only)
    """
    try:
        user = update.effective_user
        
        # Simple admin check
        OWNER_ID = [int(x) for x in os.getenv("OWNER_ID", "").split(",") if x.strip()]
        
        if user.id not in OWNER_ID:
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        # Get all clone bots
        clone_bots = await clone_bots_collection.find({}).sort("created_at", -1).to_list(length=50)
        
        if not clone_bots:
            await update.message.reply_text("📝 No clone bots found.")
            return
        
        text = f"🤖 *Clone Bots List* \\({len(clone_bots)} total\\)\\n\\n"
        
        for i, bot in enumerate(clone_bots[:10], 1):  # Show first 10
            text += f"{i}\\. @{bot.get('bot_username', 'Unknown')}\\n"
            text += f"   • *Owner:* `{bot.get('user_id')}`\\n"
            
            # Handle date formatting separately to avoid f-string backslash issue
            created_date = bot.get('created_at')
            if created_date:
                date_str = created_date.strftime('%Y-%m-%d')
                text += f"   • *Created:* {date_str}\\n"
            else:
                text += f"   • *Created:* Unknown\\n"
                
            text += f"   • *Status:* {bot.get('status', 'Unknown')}\\n\\n"
        
        if len(clone_bots) > 10:
            text += f"\\.\\.\\. and {len(clone_bots) - 10} more"
        
        await update.message.reply_text(text, parse_mode="Markdown")
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ List Clone Bots Error:*\\n`{str(e)}`\\n```{traceback.format_exc()}```"
        )
        await update.message.reply_text("❌ Error retrieving clone bots list.")

def setup(app: Application) -> None:
    """
    Setup function called by the main bot to register handlers
    """
    app.add_handler(CommandHandler("clonebot", clone_bot_command))
    app.add_handler(CommandHandler("listclones", list_clone_bots))

async def test() -> None:
    """
    Test function to verify the plugin works correctly
    """
    # Test database connection
    await db.command("ping")
    
    # Test that collections exist
    collections = await db.list_collection_names()
    if "clone_bots" not in collections:
        # Create the collection if it doesn't exist
        await clone_bots_collection.create_index("user_id", unique=True)

def get_info() -> dict:
    """
    Return plugin information
    """
    return {
        "name": "Clone Bot",
        "description": "Allows users to create their own bot instances",
        "version": "1.0.0",
        "commands": [
            "/clonebot <token> - Create a clone bot with your token",
            "/listclones - List all clone bots (admin only)"
        ]
    }
    
    async def _create_clone_main_py(self, bot_dir: str, owner_id: int, bot_username: str):
        """
        Create a modified main.py for clone bots that reports errors to main support
        """
        main_py_content = f'''import os
import importlib
import asyncio
import logging
import traceback
from typing import Dict, Any
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ----------- Logging -----------
logging.basicConfig(
    filename="bot.log",
    format="%(asctime)s - %(message)s",
    level=logging.INFO
)

# ----------- Load .env -----------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")
CLONE_OWNER_ID = {owner_id}

# Error reporting bot (main bot)
error_bot = Bot(token=os.getenv("MAIN_BOT_TOKEN", TOKEN))

async def send_clone_error_to_support(text: str):
    """Send clone bot errors to main support chat"""
    try:
        error_message = f"🤖 *Clone Bot Error (@{bot_username})*\\n"
        error_message += f"*Owner:* `{CLONE_OWNER_ID}`\\n\\n"
        error_message += text
        
        await error_bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=error_message[:4000],
            parse_mode="MarkdownV2"
        )
    except Exception:
        pass

PLUGINS: Dict[str, Dict[str, Any]] = {{}}

# ----------- Static Text Loaders -----------
def load_text_file(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"⚠️ Error loading {{filename}}: {{e}}"

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

    for file in os.listdir(plugin_dir):
        if file.endswith(".py") and file != "__init__.py":
            name = file[:-3]
            try:
                module = importlib.import_module(f"{{plugin_dir}}.{{name}}")

                if hasattr(module, "setup"):
                    module.setup(app)

                if hasattr(module, "test"):
                    try:
                        await module.test()
                    except Exception as test_err:
                        await send_clone_error_to_support(
                            f"*❌ Plugin `{{name}}` test failed:*\\n`{{test_err}}`\\n```{{traceback.format_exc()}}```"
                        )
                        continue

                if hasattr(module, "get_info"):
                    PLUGINS[name] = module.get_info() or {{}}

            except Exception as e:
                await send_clone_error_to_support(
                    f"*❌ Plugin `{{name}}` load error:*\\n`{{e}}`\\n```{{traceback.format_exc()}}```"
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
        return

# ----------- Error Handler -----------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and send to support"""
    try:
        error_text = f"*❌ Clone Bot Error:*\\n`{{str(context.error)}}`\\n```{{traceback.format_exc()}}```"
        await send_clone_error_to_support(error_text)
    except Exception:
        pass

# ----------- Main Function -----------
def main():
    if not TOKEN:
        raise RuntimeError("❌ BOT_TOKEN is not set.")

    application = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()

    # Add error handler
    application.add_error_handler(error_handler)

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(info|help|main_menu)$"))

    async def post_init(app: Application):
        await load_plugins(app)
        try:
            await send_clone_error_to_support(f"✅ *Clone bot @{bot_username} started successfully*")
        except Exception:
            pass

    # Set post-init tasks
    application.post_init = post_init

    print("🚀 Clone Bot is starting...")
    logging.info("🚀 Clone Bot is running.")
    application.run_polling()

if __name__ == "__main__":
    main()
'''
        
        with open(f"{bot_dir}/main.py", "w") as f:
            f.write(main_py_content)

# Global clone bot manager instance
clone_manager = CloneBotManager()

async def clone_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /clonebot command
    """
    try:
        user = update.effective_user
        
        if not context.args:
            help_text = """🤖 *Clone Bot Creator*

To create your own bot instance, use:
`/clonebot YOUR_BOT_TOKEN`

*How to get a bot token:*
1\\. Message @BotFather on Telegram
2\\. Send `/newbot`
3\\. Follow the instructions to create your bot
4\\. Copy the token and use it with this command

*Example:*
`/clonebot 123456789:ABCdefGHIjklMNOpqrSTUvwxyz`

⚠️ *Important:*
• Keep your token private
• Your clone bot will have the same features as this bot
• All errors will be reported to our support team
• You can update your clone bot by running the command again"""

            await update.message.reply_text(help_text, parse_mode="MarkdownV2")
            return
        
        bot_token = context.args[0].strip()
        
        # Validate token format
        if not bot_token or ":" not in bot_token:
            await update.message.reply_text(
                "❌ Invalid token format. Please provide a valid bot token from @BotFather."
            )
            return
        
        # Show processing message
        processing_msg = await update.message.reply_text("🔄 Creating your clone bot... Please wait.")
        
        # Create clone bot
        result = await clone_manager.create_clone_bot(
            user_id=user.id,
            bot_token=bot_token,
            user_name=user.first_name or user.username or str(user.id)
        )
        
        if result["success"]:
            success_text = f"""✅ *Clone Bot Created Successfully!*

🤖 *Bot Username:* @{result['bot_username']}
🆔 *Bot ID:* `{result['bot_id']}`

Your bot is now ready to use! You can:
• Add it to groups
• Use all the same commands as this bot
• Customize it further if needed

*Note:* Your bot will start automatically. All errors and logs will be forwarded to our support team for monitoring."""

            await processing_msg.edit_text(success_text, parse_mode="MarkdownV2")
            
            # Log to support
            await send_log(
                f"🤖 *New Clone Bot Created*\\n"
                f"• *Owner:* {user.first_name or 'N/A'} \\(@{user.username or 'N/A'}\\)\\n"
                f"• *Owner ID:* `{user.id}`\\n"
                f"• *Bot:* @{result['bot_username']}\\n"
                f"• *Bot ID:* `{result['bot_id']}`"
            )
            
        else:
            await processing_msg.edit_text(result["message"])
            
            # Log error to support
            await send_error_to_support(
                f"*❌ Clone Bot Creation Failed*\\n"
                f"• *User:* {user.first_name or 'N/A'} \\(@{user.username or 'N/A'}\\)\\n"
                f"• *User ID:* `{user.id}`\\n"
                f"• *Error:* `{result.get('error', 'Unknown error')}`"
            )
            
    except Exception as e:
        await send_error_to_support(
            f"*❌ Clone Bot Command Error:*\\n`{str(e)}`\\n```{traceback.format_exc()}```"
        )
        await update.message.reply_text("❌ An error occurred while creating your clone bot. Please try again later.")

async def list_clone_bots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    List all clone bots (admin only)
    """
    try:
        user = update.effective_user
        
        # Simple admin check
        OWNER_ID = [int(x.strip()) for x in os.getenv("OWNER_ID", "").split(",") if x.strip()]
        
        if user.id not in OWNER_ID:
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
        
        # Get all clone bots
        clone_bots = await clone_bots_collection.find({}).sort("created_at", -1).to_list(length=50)
        
        if not clone_bots:
            await update.message.reply_text("📝 No clone bots found.")
            return
        
        text = f"🤖 *Clone Bots List* \\({len(clone_bots)} total\\)\\n\\n"
        
        for i, bot in enumerate(clone_bots[:10], 1):  # Show first 10
            text += f"{i}\\. @{bot.get('bot_username', 'Unknown')}\\n"
            text += f"   • *Owner:* `{bot.get('user_id')}`\\n"
            
            # Handle date formatting separately to avoid f-string backslash issue
            created_date = bot.get('created_at')
            if created_date:
                date_str = created_date.strftime('%Y-%m-%d')
                text += f"   • *Created:* {date_str}\\n"
            else:
                text += f"   • *Created:* Unknown\\n"
                
            text += f"   • *Status:* {bot.get('status', 'Unknown')}\\n\\n"
        
        if len(clone_bots) > 10:
            text += f"\\.\\.\\. and {len(clone_bots) - 10} more"
        
        await update.message.reply_text(text, parse_mode="MarkdownV2")
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ List Clone Bots Error:*\\n`{str(e)}`\\n```{traceback.format_exc()}```"
        )
        await update.message.reply_text("❌ Error retrieving clone bots list.")

def setup(app: Application) -> None:
    """
    Setup function called by the main bot to register handlers
    """
    app.add_handler(CommandHandler("clonebot", clone_bot_command))
    app.add_handler(CommandHandler("listclones", list_clone_bots))

async def test() -> None:
    """
    Test function to verify the plugin works correctly
    """
    # Test database connection
    await db.command("ping")
    
    # Test that collections exist
    collections = await db.list_collection_names()
    if "clone_bots" not in collections:
        # Create the collection if it doesn't exist
        await clone_bots_collection.create_index("user_id", unique=True)

def get_info() -> dict:
    """
    Return plugin information
    """
    return {
        "name": "Clone Bot",
        "description": "Allows users to create their own bot instances",
        "version": "1.0.0",
        "commands": [
            "/clonebot <token> - Create a clone bot with your token",
            "/listclones - List all clone bots (admin only)"
        ]
    }

