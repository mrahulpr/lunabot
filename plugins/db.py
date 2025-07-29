import os
from motor.motor_asyncio import AsyncIOMotorClient
import traceback
from telegram import Bot

# ENV VARS
MONGO_URI = os.getenv("MONGO_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")  # Can be group ID or user ID

# Placeholder for DB client
db = None

# Safe async init function to be called in your main
async def init_db():
    global db
    try:
        if not MONGO_URI:
            raise ValueError("MONGO_URI is not set.")

        # Connect to MongoDB using Motor
        client = AsyncIOMotorClient(MONGO_URI)
        db = client["telegram_bot"]  # Change this name if needed

        # Try a test command to confirm connection
        await db.command("ping")

    except Exception as e:
        error_text = (
            "❗️ *Database Initialization Failed*\n"
            f"`{str(e)}`\n\n"
            f"```{traceback.format_exc()}```"
        )
        await send_error_to_support(error_text)

# Send detailed error logs to your support chat
async def send_error_to_support(text: str):
    if not BOT_TOKEN or not SUPPORT_CHAT_ID:
        print("⚠️ BOT_TOKEN or SUPPORT_CHAT_ID not set for logging.")
        return

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=SUPPORT_CHAT_ID, text=text[:4000], parse_mode="Markdown")
    except Exception as e:
        print("❌ Failed to send error log to support chat:", e)
