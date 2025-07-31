from datetime import datetime
import traceback
import os
from telegram import Update, Bot
from telegram.ext import CommandHandler, ContextTypes
from plugins.db import db  # ✅ Corrected import

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")


async def send_error_to_support(error: Exception, where="sample_plugin"):
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


# /sample command
async def sample_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat
        message = update.message

        data = {
            "chat_id": chat.id,
            "user_id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "message": " ".join(context.args) if context.args else "No message",
            "timestamp": datetime.utcnow()
        }

        await db.samples.insert_one(data)

        await message.reply_text(
            f"✅ Sample stored for *{user.first_name}*\\.\n📝 Message: `{data['message']}`",
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        await send_error_to_support(e, "sample_command")


# /samplelog command
async def sample_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        cursor = db.samples.find({"chat_id": chat_id}).sort("timestamp", -1).limit(3)

        messages = []
        async for entry in cursor:
            full_name = entry.get("full_name", "Unknown").replace("_", "\\_")
            msg = entry.get("message", "").replace("_", "\\_")
            messages.append(f"👤 *{full_name}* → `{msg}`")

        await update.message.reply_text(
            "\n\n".join(messages) if messages else "📭 No entries found\\.",
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        await send_error_to_support(e, "sample_show")


# Optional metadata
def get_info():
    return {
        "name": "Sample Plugin 🧩",
        "description": "Template plugin with MongoDB support for logging user input."
    }


# Required setup function
def setup(app):
    app.add_handler(CommandHandler("sample", sample_command))
    app.add_handler(CommandHandler("samplelog", sample_show))
