import os
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import CommandHandler, ContextTypes
from plugins.db import db

OWNER_ID = int(os.getenv("OWNER_ID"))
SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID"))

def setup(app):
    app.add_handler(CommandHandler("getdata", get_data))
    app.add_handler(CommandHandler("keys", list_keys))

async def get_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != SUPPORT_CHAT_ID:
        return await update.message.reply_text("❌ This command only works in the *support chat*", parse_mode="MarkdownV2")

    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 You are not authorized to use this command.")

    if not context.args:
        return await update.message.reply_text("❌ Usage: /getdata `<key>`", parse_mode="MarkdownV2")

    key = context.args[0]
    data = await db.bot_data.find_one({"_id": key})

    if not data:
        return await update.message.reply_text(f"❌ No data found for `{key}`", parse_mode="MarkdownV2")

    data.pop("_id", None)
    content = str(data)

    try:
        formatted = f"*🔍 Data for `{key}`:*\n```{content}```"
        if len(formatted) < 3500:
            await update.message.reply_text(formatted, parse_mode="MarkdownV2")
        else:
            raise ValueError("Too long")
    except Exception:
        # Fallback to text file
        file = BytesIO(content.encode("utf-8"))
        file.name = f"{key}_data.txt"
        await update.message.reply_document(
            document=InputFile(file),
            caption=f"📄 Data for `{key}`",
            parse_mode="MarkdownV2"
        )

async def list_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != SUPPORT_CHAT_ID:
        return await update.message.reply_text("❌ This command only works in the *support chat*", parse_mode="MarkdownV2")

    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 You are not authorized to use this command.")

    keys_cursor = db.bot_data.find({}, {"_id": 1})
    keys = [doc["_id"] async for doc in keys_cursor]

    if not keys:
        return await update.message.reply_text("❌ No keys found in the database.")

    formatted_keys = "\n".join(f"• `{k}`" for k in keys)
    await update.message.reply_text(f"*🗂️ Available Keys:*\n{formatted_keys}", parse_mode="MarkdownV2")
