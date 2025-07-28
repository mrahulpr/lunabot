from telegram import Update, MessageReactionTypeEmoji
from telegram.ext import CommandHandler, ContextTypes

async def react_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # Must reply to a message
    if not message or not message.reply_to_message:
        await message.reply_text("⚠️ Please reply to a message you want to react to.")
        return

    # Extract emoji from command args
    if context.args:
        emoji = context.args[0]
    else:
        emoji = "🔥"  # Default if no emoji given

    try:
        await message.reply_to_message.react(
            [MessageReactionTypeEmoji(emoji=emoji)]
        )
        await message.reply_text(f"✅ Reacted with {emoji}")
    except Exception as e:
        await message.reply_text(f"❌ Failed to react: {e}")

def get_info():
    return {
        "name": "React 🔥",
        "description": "React to a replied message with custom emoji. Usage: `/react 😂` (must be a reply)"
    }

def setup(app):
    app.add_handler(CommandHandler("react", react_command))
