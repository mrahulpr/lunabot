# plugin/db.py (FIXED VERSION)

import os
from motor.motor_asyncio import AsyncIOMotorClient
import traceback
from telegram import Bot

MONGO_URI = os.getenv("MONGO_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")

db = None

async def init_db():
    global db
    try:
        if not MONGO_URI:
            raise ValueError("MONGO_URI is not set.")

        client = AsyncIOMotorClient(MONGO_URI)
        db = client["telegram_bot"]
        await db.command("ping")

        success_text = (
            "✅ *Successfully connected to MongoDB*\n"
            "`Connection verified with ping command.`"
        )
        await send_error_to_support(success_text)

    except Exception as e:
        error_text = (
            "❗️ *Database Initialization Failed*\n"
            f"`{str(e)}`\n\n"
            "```" + traceback.format_exc() + "```"
        )
        await send_error_to_support(error_text)

async def send_error_to_support(text: str):
    if not BOT_TOKEN or not SUPPORT_CHAT_ID:
        return

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=SUPPORT_CHAT_ID, text=text[:4000], parse_mode="MarkdownV2")
    except Exception:
        pass
