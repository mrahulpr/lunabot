import os
import traceback
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Bot

# Environment variables
MONGO_URI = os.getenv("MONGO_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")

# Global DB instance
db = None

# Send a message to the support chat
async def send_to_support(text: str):
    if not BOT_TOKEN or not SUPPORT_CHAT_ID:
        return
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=text[:4000],
            parse_mode="MarkdownV2"
        )
    except:
        # Silently ignore logging errors
        pass

# Initialize the database
async def init_db():
    global db
    try:
        if not MONGO_URI:
            raise ValueError("MONGO_URI is not set\\.")

        client = AsyncIOMotorClient(MONGO_URI)
        db = client["telegram_bot"]

        # Test connection
        await db.command("ping")

        await send_to_support("✅ *Connected to MongoDB successfully*")

    except Exception as e:
        error_text = (
            "❗️ *Database Initialization Failed*\n"
            f"`{str(e).replace('`', '\\`')}`\n\n"
            f"```{traceback.format_exc().replace('`', '\\`')}```"
        )
        # Escape MarkdownV2 special characters
        escaped = (
            error_text
            .replace("_", "\\_")
            .replace("-", "\\-")
            .replace(".", "\\.")
        )
        await send_to_support(escaped)
