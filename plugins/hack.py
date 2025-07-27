import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

async def hack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🧠 Initiating hack...")

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
        "*✅ Hack Complete\\!*\\n"
        "🔒 *Data archived\\.\\n*"
        "📄 *Download link:*\\"
        "[Open file](https://drive.google.com/file/d/1JNA0HY1v8ClBDU9PhmyQ-z8KuLgvteT5/view?usp=sharing)"
    )
    await msg.edit_text(final_msg, parse_mode="MarkdownV2")

async def hack_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="help")]]
    text = (
        "💻 *Hack Plugin*\n\n"
        "Simulates a fake hacking sequence as a prank\\.\n\n"
        "*Usage:*\n"
        "`/hack` \\– triggers the hacking animation\\.\n"
    )
    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard))

def get_info():
    return {
        "name": "Hack 💻",
        "description": "Simulates a fake hacking prank with animations."
    }

def setup(app):
    app.add_handler(CommandHandler("hack", hack))
    app.add_handler(CallbackQueryHandler(hack_help_callback, pattern="^plugin::hack$"))
