import os
from telegram import Update
from telegram.ext import ContextTypes

commands = ['restart']

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) == os.getenv("OWNER_ID"):
        await update.message.reply_text("🔄 Restarting bot...")
        os._exit(0)
    else:
        await update.message.reply_text("❌ You are not authorized to use this command.")
