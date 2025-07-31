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
            "🧠 Initiating hack...",
            reply_to_message_id=update.message.reply_to_message.message_id
        )

        await asyncio.sleep(1)
        await msg.edit_text("Installing Files To Hacked Private Server...\nTarget Selected...\nInstalling... 20%")
        await asyncio.sleep(1.2)
        await msg.edit_text("Installing... 52%\n█████████▒▒▒▒\nUploading payload to remote server...")
        await asyncio.sleep(1.2)
        await msg.edit_text("🧬 Connecting to Telegram internal APIs...")

        await asyncio.sleep(1.2)
        await msg.edit_text(
            "```root@anon:~# ls\nusr/ ghost/ codes/\ntouch exploit.sh\nexecuting exploit...\nextracting tokens...```",
            parse_mode="MarkdownV2"
        )

        await asyncio.sleep(1.5)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📄 Open Hacked File", url="https://drive.google.com/file/d/1JNA0HY1v8ClBDU9PhmyQ-z8KuLgvteT5/view?usp=sharing")
        ]])
        await msg.edit_text(
            "*✅ Hack Complete\\!*\n🔒 *Data archived\\.*",
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )

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
        "description": "Simulates a Real hacking prank with animations. Works only as a reply."
    }

async def test():
    pass

def setup(app):
    app.add_handler(CommandHandler("hack", hack))
    app.add_handler(CallbackQueryHandler(hack_help_callback, pattern="^plugin::hack$"))
