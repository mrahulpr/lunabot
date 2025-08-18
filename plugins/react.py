import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReactionTypeEmoji
from telegram.ext import ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from plugins.db import send_error_to_support, db

# Default emojis for reactions
EMOJIS = ["👍","👎","❤️","😆","😯","😢","😡","🎉","🤯","😱","👏","🤔","🤩","🤮"]

# --- Admin helper ---
async def is_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# --- Reaction to message ---
async def react_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or update.message.from_user.is_bot:
            return

        chat = update.effective_chat
        if chat.type == "private":
            return  # only groups

        chat_id = chat.id
        chat_settings = await db.reacts.find_one({"chat_id": chat_id})
        if not chat_settings or not chat_settings.get("enabled", True):
            return

        text = update.message.text.lower() if update.message.text else ""
        emoji = None

        # Context-aware reactions
        if any(word in text for word in ["hi", "hello", "hey"]):
            emoji = "😆"
        elif any(word in text for word in ["lol", "lmao", "haha", "rofl"]):
            emoji = "😆"
        elif any(word in text for word in ["bye", "good night", "gn"]):
            emoji = random.choice(["😆", "👍"])
        elif any(word in text for word in ["love", "❤", "❤️"]):
            emoji = "💔"
        elif "?" in text:
            emoji = "🤔"
        else:
            emoji = random.choice(EMOJIS)

        await update.message.set_reaction([ReactionTypeEmoji(emoji=emoji)])

    except Exception as e:
        await send_error_to_support(f"⚠️ Error in react_message:\n{e}")

# --- /reacts command ---
async def reacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = update.effective_chat
        if chat.type == "private":
            await update.message.reply_text("🚫 This command works in groups only.")
            return

        user_id = update.effective_user.id
        if not await is_admin(context, chat.id, user_id):
            await update.message.reply_text("⚠️ Only admins can manage reactions.")
            return

        chat_settings = await db.reacts.find_one({"chat_id": chat.id})
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

# --- Callback for inline toggle ---
async def reacts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        chat_id = query.message.chat.id
        user_id = query.from_user.id
        if not await is_admin(context, chat_id, user_id):
            return await query.answer("⚠️ Only admins can toggle reactions.", show_alert=True)

        new_status = True if query.data == "reacts_enable" else False
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
        "name": "React Plugin 🎭",
        "description": "Auto-reacts to group messages with emojis. Admins can toggle using /reacts."
    }

# --- Setup ---
def setup(app):
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, react_message))
    app.add_handler(CommandHandler("reacts", reacts_command))
    app.add_handler(CallbackQueryHandler(reacts_callback, pattern=r"^reacts_"))

# --- Test ---
async def test():
    return "✅ React plugin loaded successfully"
