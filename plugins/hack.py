import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from .db import send_error_to_support  # log any errors

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

        animation_1 = [
            " Installing Files To Hacked Private Server...",
            " Target Selected.",
            " Installing... 4%\n█▒▒▒▒▒▒▒▒▒▒▒▒",
            " Installing... 20%\n███▒▒▒▒▒▒▒▒▒▒",
            " Installing... 52%\n█████████▒▒▒▒",
            " Installing... 100%\n████████████",
            " Uploading payload to remote server...",
        ]
        for line in animation_1:
            await asyncio.sleep(0.7)
            await msg.edit_text(line)

        await asyncio.sleep(1)
        await msg.edit_text("🧬 Connecting to Telegram internal APIs...")

        animation_2 = [
            "`root@anon:~# ls`",
            "`usr/ ghost/ codes/`",
            "`touch exploit.sh`",
            "`exploit.sh deployed.`",
            "`executing exploit...`",
            "`extracting tokens...`",
            "`dumping messages...`",
            "`creating pdf of chat logs...`"
        ]
        for line in animation_2:
            await asyncio.sleep(0.6)
            await msg.edit_text(line, parse_mode="MarkdownV2")

        await asyncio.sleep(1.5)
        final_msg = (
            "*✅ Hack Complete\\!*\n"
            "🔒 *Data archived\\.*\n"
            "📄 *Download link:* [Open file](https://drive.google.com/file/d/1JNA0HY1v8ClBDU9PhmyQ-z8KuLgvteT5/view?usp=sharing)"
        )
        await msg.edit_text(final_msg, parse_mode="MarkdownV2")

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
        "description": "Simulates a fake hacking prank with animations. Works only as a reply."
    }

async def test():
    # No database or required preconditions to test
    pass

def setup(app):
    app.add_handler(CommandHandler("hack", hack))
    app.add_handler(CallbackQueryHandler(hack_help_callback, pattern="^plugin::hack$"))
