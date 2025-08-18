import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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


# --- Main reaction handler ---
async def react_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    try:
        if chat.type == "private":
            await update.message.reply_text("🚫 This command works in groups only.")
            return
        
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

        # ✅ FIX: use list of strings, not dicts
        await context.bot.setMessageReaction(
            chat_id=chat_id,
            message_id=update.message.message_id,
            reaction=[emoji],
        )

    except Exception as e:
        await send_error_to_support(f"⚠️ Error in react plugin:\n{e}")


# --- Command to manage reacts with inline buttons ---
async def reacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        if not await is_admin(context, chat_id, user_id):
            return await update.message.reply_text("⚠️ Only admins can manage reactions.")

        chat_settings = await db.reacts.find_one({"chat_id": chat_id})
        enabled = chat_settings.get("enabled", True) if chat_settings else True

        text = f"⚙️ Reactions are currently {'✅ enabled' if enabled else '❌ disabled'}."
        buttons = [
            [
                InlineKeyboardButton("✅ Enable", callback_data="reacts_enable"),
                InlineKeyboardButton("❌ Disable", callback_data="reacts_disable"),
            ]
        ]

        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        await send_error_to_support(f"⚠️ Error in reacts_command:\n{e}")


# --- Callback handler for inline toggle ---
async def reacts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat.id
        user_id = query.from_user.id

        if not await is_admin(context, chat_id, user_id):
            return await query.answer("⚠️ Only admins can toggle reactions.", show_alert=True)

        if query.data == "reacts_enable":
            new_status = True
        elif query.data == "reacts_disable":
            new_status = False
        else:
            return

        await db.reacts.update_one(
            {"chat_id": chat_id},
            {"$set": {"enabled": new_status}},
            upsert=True
        )

        text = f"✅ Reactions are now {'enabled' if new_status else 'disabled'}."
        buttons = [
            [
                InlineKeyboardButton("✅ Enable", callback_data="reacts_enable"),
                InlineKeyboardButton("❌ Disable", callback_data="reacts_disable"),
            ]
        ]

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        await send_error_to_support(f"⚠️ Error in reacts_callback:\n{e}")


# --- Info ---
def get_info():
    return {
        "name": "React Plugin",
        "description": "Reacts to every message with context-aware emojis. Admins can toggle with /reacts."
    }


# --- Setup ---
def setup(app):
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, react_message))
    app.add_handler(CommandHandler("reacts", reacts_command))
    app.add_handler(CallbackQueryHandler(reacts_callback, pattern=r"^reacts_"))


# --- Test ---
async def test():
    return "✅ React plugin loaded successfully"
