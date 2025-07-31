import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
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

        msg = await update.message.reply_text(
            "🧠 *Initiating hack sequence...*",
            parse_mode="MarkdownV2",
            reply_to_message_id=update.message.reply_to_message.message_id
        )

        log = []
        steps = [
            "🔍 Scanning target...",
            "✅ Target locked.",
            "💻 Connecting to secured server...",
            "🔐 Bypassing firewall (Layer 1)...",
            "🔐 Bypassing firewall (Layer 2)...",
            "🔐 Bypassing firewall (Layer 3)...",
            "🔓 Access granted.",
            "📁 Installing backdoor...",
            "📡 Uploading payload...",
            "📦 Installing... 10%\n████▒▒▒▒▒▒▒▒",
            "📦 Installing... 25%\n██████▒▒▒▒▒▒",
            "📦 Installing... 67%\n███████████▒",
            "📦 Installing... 95%\n█████████████▒",
            "📦 Installing... 100%\n██████████████",
            "💣 Executing remote exploit...",
            "`anon@ghost:~$ ls -a`",
            "`ghost/ exploit.sh  secrets.txt`",
            "`chmod +x exploit.sh`",
            "`./exploit.sh --run`",
            "`Extracting Telegram tokens...`",
            "`Decrypting chat history...`",
            "`Packing logs...`",
        ]

        for step in steps:
            log.append(step)
            text = "\n".join(log)
            await msg.edit_text(text, parse_mode="MarkdownV2")
            await asyncio.sleep(0.9)

        await asyncio.sleep(1.5)

        final_text = "*✅ Hack Complete\\!*\n🔒 *All data archived successfully\\.*"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📁 Open Hacked File", url="https://drive.google.com/file/d/1JNA0HY1v8ClBDU9PhmyQ-z8KuLgvteT5/view?usp=sharing")
        ]])
        await msg.edit_text(final_text, parse_mode="MarkdownV2", reply_markup=keyboard)

    except Exception as e:
        import traceback
        await send_error_to_support(f"*❌ Error in hack plugin:*\n`{e}`\n```{traceback.format_exc()}```")

async def hack_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="help")]]
        text = (
            "💻 *Hack Plugin*\n\n"
            "Simulates a fake hacking sequence as a prank\\.\n\n"
            "*Usage:*\n"
            "`/hack` – Reply to a user's message to initiate a fake hack\\.\n"
        )
        await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        import traceback
        await send_error_to_support(f"*❌ Hack help button error:*\n`{e}`\n```{traceback.format_exc()}```")

def get_info():
    return {
        "name": "Hack 💻",
        "description": "Simulates a fake hacking prank with cascading terminal animation. Works only as a reply."
    }

async def test():
    pass

def setup(app):
    app.add_handler(CommandHandler("hack", hack))
    app.add_handler(CallbackQueryHandler(hack_help_callback, pattern="^plugin::hack$"))
