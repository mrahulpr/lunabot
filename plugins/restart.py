from telegram import Update
from telegram.ext import ContextTypes
import os
import sys

commands = ["restart"]

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != os.getenv("OWNER_ID"):
        await update.message.reply_text("⛔ You're not allowed to use this.")
        return
    await update.message.reply_text("♻️ Restarting bot...")
    await context.bot.send_message(chat_id=update.effective_user.id, text="🔄 Bot restarted by owner.")
    os.execv(sys.executable, ['python'] + sys.argv)