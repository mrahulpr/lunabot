from telegram import Update
from telegram.ext import ContextTypes

commands = ['echo']

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args)
    await update.message.reply_text(text if text else "Nothing to echo!")
