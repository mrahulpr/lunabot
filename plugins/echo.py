from telegram import Update
from telegram.ext import ContextTypes

commands = ["echo"]

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🗣 Usage: `/echo <your message>`", parse_mode="Markdown")
        return
    message = " ".join(context.args)
    await update.message.reply_text(f"🔁 {message}")