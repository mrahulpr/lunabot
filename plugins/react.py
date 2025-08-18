import random
import emoji  # external package: pip install emoji
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from plugins.db import send_error_to_support

async def react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """React with a random emoji from the entire emoji set"""
    try:
        all_emojis = list(emoji.EMOJI_DATA.keys())
        chosen = random.choice(all_emojis)

        await context.bot.set_message_reaction(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            reaction=[{"type": "emoji", "emoji": chosen}],
        )
    except Exception as e:
        await send_error_to_support(f"⚠️ Error in react plugin:\n{e}")

def setup(app):
    app.add_handler(MessageHandler(filters.ALL, react))

def get_info():
    return {"name": "react", "description": "Reacts with a random emoji"}

async def test():
    return "✅ React plugin loaded successfully"
