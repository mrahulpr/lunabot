import asyncio
import os
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import RetryAfter
from .db import send_error_to_support

OWNER_ID = int(os.getenv("OWNER_ID"))

async def hack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.reply_to_message:
            return await update.message.reply_text("⚠️ You must reply to someone's message to use this command.")

        target = update.message.reply_to_message.from_user
        bot = context.bot
        me = await bot.get_me()

        if target.id == me.id:
            return await update.message.reply_text("🤖 I don't hack myself... nice try 😂.")
        if target.id == OWNER_ID:
            return await update.message.reply_text("🫣 I will hack my owner... please don't tell him!")

        await bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        msg = await update.message.reply_text("🧠 Initiating hack...", reply_to_message_id=update.message.reply_to_message.message_id)

        steps = [
            "🔍 Scanning target...",
            "🎯 Target locked",
            "🔗 Connecting to secured server...",
            "🛡️ Bypassing firewall 1...",
            "🛡️ Bypassing firewall 2...",
            "🛡️ Bypassing firewall 3...",
            "💾 Installing... 10% 🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜",
            "💾 Installing... 25% 🟩🟩⬜⬜⬜⬜⬜⬜⬜⬜",
            "💾 Installing... 67% 🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜",
            "💾 Installing... 95% 🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜",
            "💾 Installing... 100% 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩",
            "🚀 Payload deployed",
            "📦 Extracting data...",
            "💬 Dumping messages...",
            "📄 Generating PDF report...",
        ]

        buffer = []
        max_lines = 5

        for line in steps:
            buffer.append(line)
            if len(buffer) > max_lines:
                buffer.pop(0)

            quoted = "\n".join(f"> {l}" for l in buffer)

            while True:
                try:
                    await msg.edit_text(quoted)
                    break
                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after + 1)

            await asyncio.sleep(0.9)

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📄 View Hacked File", url="https://drive.google.com/file/d/1JNA0HY1v8ClBDU9PhmyQ-z8KuLgvteT5/view?usp=sharing")]]
        )
        await msg.edit_text("✅ Hack complete. Data archived.", reply_markup=keyboard)

    except Exception as e:
        tb = traceback.format_exc()
        await send_error_to_support(f"*❌ Error in hack plugin:*\n`{e}`\n```{tb}```")

async def hack_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="help")]]
        text = (
            "💻 Hack Plugin\n\n"
            "Simulates a fake hacking sequence as a prank.\n\n"
            "Usage:\n"
            "`/hack` – Reply to a user's message to prank-hack them."
        )
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        tb = traceback.format_exc()
        await send_error_to_support(f"*❌ Hack help button error:*\n`{e}`\n```{tb}```")

def get_info():
    return {
        "name": "Hack 💻",
        "description": "Fake hacking animation as prank. Must reply to a user."
    }

async def test():
    pass

def setup(app):
    app.add_handler(CommandHandler("hack", hack))
    app.add_handler(CallbackQueryHandler(hack_help_callback, pattern="^plugin::hack$"))
