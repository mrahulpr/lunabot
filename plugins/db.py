import os
import traceback
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Bot

MONGO_URI = os.getenv("MONGO_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")

client = AsyncIOMotorClient(MONGO_URI)
db = client["telegram_bot"]
bot = Bot(token=BOT_TOKEN)

async def init():
    try:
        await db.command("ping")
        await send_log("✅ *MongoDB connection successful\\.*\n`ping` responded properly\\.")
    except Exception as e:
        await send_error_to_support(
            f"*❌ MongoDB Init Failed:* `{str(e)}`\n```{traceback.format_exc()}```"
        )
        raise  # Fail fast if DB doesn't connect

async def test():
    await db.command("ping")  # Used by plugin loader to validate DB connection

async def send_error_to_support(text: str):
    try:
        await bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=text[:4000],
            parse_mode="MarkdownV2"
        )
    except Exception:
        pass

async def send_log(text: str):
    try:
        await bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=text[:4000],
            parse_mode="MarkdownV2"
        )
    except Exception:
        pass
