import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from .db import send_error_to_support  # Import your error handler

async def hack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.reply_to_message:
            return await update.message.reply_text("⚠️ You must reply to someone's message to use this command.")

        target = update.message.reply_to_message.from_user
        bot = context.bot
        me = await bot.get_me()

        if target.id == me.id:
            return await update.message.reply_text("🤖 I don't hack myself... nice try 😂.")
        
        if target.id == int(context.bot_data.get("OWNER_ID", 0)):
            return await update.message.reply_text("🫣 I will hack my owner... please don't tell him!")

        msg = await update.message.reply_text("> Initializing hack sequence...", parse_mode=None)

        animation = [
            "Scanning target...",
            "Target locked.",
            "Connecting to secured server...",
            "Bypassing firewall 1...",
            "Bypassing firewall 2...",
            "Bypassing firewall 3...",
            "Installing payload... 10% 🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜",
            "Installing payload... 25% 🟩🟩⬜⬜⬜⬜⬜⬜⬜⬜",
            "Installing payload... 67% 🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜",
            "Installing payload... 95% 🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜",
            "Uploading payload...",
            "Finalizing connection...",
            "Generating exploit link...",
            "Target successfully hacked!",
        ]

        buffer = []
        for line in animation:
            buffer.append(line)
            if len(buffer) > 4:
                buffer.pop(0)

            await msg.edit_text("\n".join(f"> {l}" for l in buffer), parse_mode=None)
            await asyncio.sleep(1.2)

        await msg.edit_text(
            "> Target compromised. Click below to access the panel.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🕵️ View Hacked Panel", url="https://example.com/hacked")]]
            ),
            parse_mode=None
        )

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
            "Simulates a fake hacking sequence as a prank.\n\n"
            "*Usage:*\n"
            "`/hack` – Reply to a user's message to initiate a fake hack."
        )
        await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        import traceback
        await send_error_to_support(
            f"*❌ Hack help button error:*\n`{e}`\n```{traceback.format_exc()}```"
        )

def get_info():
    return {
        "name": "Hack 💻",
        "description": "Simulates a fake hacking prank with animations. Works only as a reply."
    }

async def test():
    pass  # No dependencies to test

def setup(app):
    app.add_handler(CommandHandler("hack", hack))
    app.add_handler(CallbackQueryHandler(hack_help_callback, pattern="^plugin::hack$"))
