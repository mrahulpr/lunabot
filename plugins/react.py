import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from plugins.db import send_error_to_support, db

# Emoji sets
EMOJIS = ["😂", "👍", "🔥", "😅", "❤️", "🤔", "🥳", "💯", "👀", "😎"]

async def is_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """Check if user is admin in group"""
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False


async def react_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return

        chat_id = update.effective_chat.id
        chat_settings = await db.reacts.find_one({"chat_id": chat_id})

        # If reactions disabled → do nothing
        if chat_settings and not chat_settings.get("enabled", True):
            return

        text = update.message.text.lower()
        emoji = None

        # Context-based reactions
        if any(word in text for word in ["hi", "hello", "hey"]):
            emoji = "👋"
        elif any(word in text for word in ["lol", "lmao", "haha", "rofl"]):
            emoji = "😂"
        elif any(word in text for word in ["bye", "good night", "gn"]):
            emoji = random.choice(["👋", "😴"])
        elif any(word in text for word in ["love", "❤", "❤️"]):
            emoji = "❤️"
        elif "?" in text:
            emoji = "🤔"
        else:
            emoji = random.choice(EMOJIS)

        await context.bot.setMessageReaction(
            chat_id=chat_id,
            message_id=update.message.message_id,
            reaction=[{"type": "emoji", "emoji": emoji}],
        )

    except Exception as e:
        await send_error_to_support(f"⚠️ Error in react plugin:\n{e}")


# --- Admin toggle command ---
async def toggle_reacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = update.effective_chat
        user = update.effective_user

        if not await is_admin(context, chat.id, user.id):
            return await update.message.reply_text("⚠️ Only admins can toggle reactions.")

        chat_settings = await db.reacts.find_one({"chat_id": chat.id})
        enabled = chat_settings.get("enabled", True) if chat_settings else True
        new_status = not enabled

        await db.reacts.update_one(
            {"chat_id": chat.id},
            {"$set": {"enabled": new_status}},
            upsert=True
        )

        await update.message.reply_text(
            f"✅ Reactions are now {'enabled' if new_status else 'disabled'} in this chat."
        )

    except Exception as e:
        await send_error_to_support(f"⚠️ Error in toggle_reacts:\n{e}")


def get_info():
    return {
        "name": "React Plugin",
        "description": "Reacts to every message with context-aware emojis. Admins can toggle with /reacts."
    }


def setup(app):
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, react_message))
    app.add_handler(CommandHandler("reacts", toggle_reacts))


async def test():
    return "✅ React plugin loaded successfully"
