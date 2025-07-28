from telegram import Update
from telegram.constants import MessageReactionTypeEmoji
from telegram.ext import CommandHandler, ContextTypes

# You can change this emoji
DEFAULT_REACTION = "🔥"

async def react_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ Reply to a message to react!")

    try:
        await update.message.reply_to_message.react(DEFAULT_REACTION)
        await update.message.reply_text(f"✅ Reacted with {DEFAULT_REACTION}")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to react: {e}")

def get_info():
    return {
        "name": "React 🔥",
        "description": "React to any replied message with an emoji. Usage: /react (as reply)"
    }

def setup(app):
    app.add_handler(CommandHandler("react", react_command))
