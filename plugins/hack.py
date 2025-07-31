import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.helpers import escape_markdown
from .db import send_error_to_support  # Must send full traceback to support

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
            escape_markdown("🧠 Initiating hack sequence...", version=2),
            parse_mode="MarkdownV2",
            reply_to_message_id=update.message.reply_to_message.message_id
        )

        # ✨ Advanced animation with fewer edits (bundled lines)
        animation_steps = [
            "🔍 Scanning target\\.\\.\\.\n🔍 Scanning target\\.\\.\\.\n🎯 Target locked\\.",
            "🔗 Connecting to secured server\\.\\.\\.\n🛡️ Bypassing firewall 1\\.\\.\\.",
            "🛡️ Bypassing firewall 2\\.\\.\\.\n🛡️ Bypassing firewall 3\\.\\.\\.",
            "📥 Installing\\.\\.\\. 10\\%\n█████▒▒▒▒▒▒\nUploading payload\\.\\.\\.",
            "📥 Installing\\.\\.\\. 25\\%\n████████▒▒▒\nInjecting backdoor\\.\\.\\.",
            "📥 Installing\\.\\.\\. 67\\%\n███████████▒\nAccessing system core\\.\\.\\.",
            "📥 Installing\\.\\.\\. 95\\%\n█████████████▒\nHijacking sessions\\.\\.\\.",
            "📥 Installing\\.\\.\\. 100\\%\n██████████████\nExfiltrating data\\.\\.\\.",
            "🧬 Connecting to Telegram internal APIs\\.\\.\\.",
            "`root@anon:~# ls`\n`usr/ ghost/ codes/`",
            "`touch exploit.sh`\n`exploit.sh deployed.`",
            "`executing exploit...`\n`extracting tokens...`",
            "`dumping messages...`\n`creating pdf of chat logs...`",
        ]

        for step in animation_steps:
            await asyncio.sleep(1.1)
            await msg.edit_text(escape_markdown(step, version=2), parse_mode="MarkdownV2")

        await asyncio.sleep(1.5)
        final_text = (
            "*✅ Hack Complete\\!*\n"
            "🔒 *Data archived\\.*"
        )
        button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📄 Open Archive", url="https://drive.google.com/file/d/1JNA0HY1v8ClBDU9PhmyQ-z8KuLgvteT5/view?usp=sharing")]]
        )
        await msg.edit_text(final_text, parse_mode="MarkdownV2", reply_markup=button)

    except Exception as e:
        import traceback
        await send_error_to_support(
            f"*❌ Error in hack plugin:*\n`{e}`\n```{traceback.format_exc()}```"
        )

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
    # No test needed here; just a dummy function
    pass

def setup(app):
    app.add_handler(CommandHandler("hack", hack))
    app.add_handler(CallbackQueryHandler(hack_help_callback, pattern="^plugin::hack$"))
