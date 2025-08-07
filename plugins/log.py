from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from config import SUPPORT_CHAT_ID
from db import db
import traceback

users_col = db["users"]

async def log_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not user:
            return

        user_data = {
            "_id": user.id,
            "full_name": user.full_name,
        }

        await users_col.update_one({"_id": user.id}, {"$set": user_data}, upsert=True)

        await context.bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=f"👤 *New user logged:*\nID: `{user.id}`\nName: `{user.full_name}`",
            parse_mode="Markdown"
        )

    except Exception as e:
        await send_error_to_support(e)

# Error reporter
async def send_error_to_support(error: Exception):
    tb = traceback.format_exc()
    from config import app
    await app.bot.send_message(chat_id=SUPPORT_CHAT_ID, text=f"*User Logger Error:*\n```{tb}```", parse_mode="Markdown")

def setup(app):
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, log_user))

def get_info():
    return {"name": "userlogger", "description": "Logs all new users to MongoDB and support chat"}

async def test():
    try:
        await db.command("ping")
    except Exception as e:
        raise RuntimeError("MongoDB not connected") from e
