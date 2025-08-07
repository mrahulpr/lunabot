from telegram import Update, Bot
from telegram.ext import MessageHandler, filters, ContextTypes
from plugins.db import db
import os
import traceback

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")


async def send_error_to_support(error: Exception, where="userlog"):
    if not BOT_TOKEN or not SUPPORT_CHAT_ID:
        return
    bot = Bot(BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=(
                f"❗️ *Plugin Error: {where}*\n"
                f"`{str(error)}`\n\n"
                f"```{traceback.format_exc()}```"
            )[:4000],
            parse_mode="MarkdownV2"
        )
    except Exception:
        pass


async def log_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not user or user.is_bot:
            return

        user_id = user.id
        full_name = user.full_name.replace("_", "\\_")

        exists = await db.users.find_one({"user_id": user_id})
        if not exists:
            await db.users.insert_one({
                "user_id": user_id,
                "full_name": user.full_name
            })

            bot = context.bot
            await bot.send_message(
                chat_id=SUPPORT_CHAT_ID,
                text=f"📃 *New User Joined*\n🆔 `{user_id}`\n👤 *Name:* {full_name}",
                parse_mode="MarkdownV2"
            )

    except Exception as e:
        await send_error_to_support(e, "log_user")


def setup(app):
    app.add_handler(MessageHandler(filters.ALL, log_user))


def get_info():
    return {
        "name": "User Logger 👤",
        "description": "Logs new users and notifies support chat."
    }


# Required plugin test() function
async def test():
    try:
        # Ping MongoDB to ensure collection is accessible
        await db.users.find_one({})
    except Exception as e:
        await send_error_to_support(e, "userlog.test")
