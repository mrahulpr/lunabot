# plugin/sample_plugin.py

from datetime import datetime
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from plugin.db import db  # 🔗 MongoDB connection

# /sample command
async def sample_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    message = update.message

    # Example data to store
    data = {
        "chat_id": chat.id,
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "message": " ".join(context.args) if context.args else "No message",
        "timestamp": datetime.utcnow()
    }

    # Save to MongoDB
    await db.samples.insert_one(data)

    await message.reply_text(
        f"✅ Sample stored for {user.first_name}.\n📝 Message: {data['message']}"
    )

# Optional command to show last 3 entries
async def sample_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cursor = db.samples.find({"chat_id": chat_id}).sort("timestamp", -1).limit(3)

    messages = []
    async for entry in cursor:
        messages.append(f"👤 {entry['full_name']} → {entry['message']}")

    await update.message.reply_text(
        "\n\n".join(messages) if messages else "📭 No entries found."
    )

# Help metadata
def get_info():
    return {
        "name": "Sample Plugin 🧩",
        "description": "Template plugin with MongoDB support for logging user input."
    }

# Register command handlers
def setup(app):
    app.add_handler(CommandHandler("sample", sample_command))
    app.add_handler(CommandHandler("samplelog", sample_show))
