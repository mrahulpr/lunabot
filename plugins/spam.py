import traceback
import os
import asyncio
from telegram import (
    Update, Bot,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler, filters,
    ContextTypes
)
from plugins.db import db  # for logging (if needed)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")

# temporary storage for pending delay requests
pending_delays = {}  # key: user_id, value: (chat_id, set_name)


async def send_error_to_support(error: Exception, where="sspam_plugin"):
    if not BOT_TOKEN or not SUPPORT_CHAT_ID:
        return
    bot = Bot(BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=(
                f"❗️ *Plugin Error: {where}*\n"
                f"`{str(error)}`\n\n"
                f"```{traceback.format_exc()}```"
            )[:4000],
            parse_mode="MarkdownV2"
        )
    except Exception:
        pass


# Step 1: /sspam command
async def sspam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.reply_to_message:
            await update.message.reply_text("⚠️ Reply to a sticker with /sspam.")
            return

        sticker_msg = update.message.reply_to_message.sticker
        if not sticker_msg:
            await update.message.reply_text("⚠️ You must reply to a *sticker* to use /sspam.")
            return

        set_name = sticker_msg.set_name
        if not set_name:
            await update.message.reply_text("⚠️ This sticker has no pack info (custom or single-use).")
            return

        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("✅ Start", callback_data=f"sspam_start:{set_name}"),
                InlineKeyboardButton("🔄 Revert", callback_data="sspam_cancel")
            ]]
        )

        await update.message.reply_text(
            f"📦 Sticker pack: *{set_name}*\nDo you want me to spam all stickers?",
            reply_markup=keyboard,
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        await send_error_to_support(e, "sspam_command")


# Step 2: Handle Start/Revert buttons
async def sspam_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        await query.answer()

        if query.data == "sspam_cancel":
            await query.edit_message_text("❌ Sticker spam cancelled.")
            return

        if query.data.startswith("sspam_start:"):
            set_name = query.data.split(":", 1)[1]
            pending_delays[user_id] = (chat_id, set_name)

            await query.edit_message_text(
                "⏱ Send me the *delay in seconds* between stickers.",
                parse_mode="MarkdownV2"
            )
    except Exception as e:
        await send_error_to_support(e, "sspam_buttons")


# Step 3: Handle delay input from user
async def sspam_delay_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        if user_id not in pending_delays:
            return  # ignore unrelated messages

        chat_id, set_name = pending_delays[user_id]

        # Only accept input in the same chat
        if update.message.chat_id != chat_id:
            return

        try:
            delay = float(update.message.text.strip())
            if delay < 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⚠️ Please enter a valid positive number.")
            return

        # delete user input message
        try:
            await update.message.delete()
        except Exception:
            pass

        del pending_delays[user_id]

        # fetch sticker set
        try:
            stickerset = await context.bot.get_sticker_set(set_name)
        except Exception as e:
            await context.bot.send_message(chat_id, "⚠️ Could not fetch sticker pack.")
            await send_error_to_support(e, "sspam_fetch")
            return

        await context.bot.send_message(
            chat_id,
            f"🚀 Starting spam with {delay} sec delay ({len(stickerset.stickers)} stickers)…"
        )

        # spam stickers with delay
        for sticker in stickerset.stickers:
            try:
                await context.bot.send_sticker(chat_id=chat_id, sticker=sticker.file_id)
                await asyncio.sleep(delay)
            except Exception as e:
                await send_error_to_support(e, "sspam_send")
    except Exception as e:
        await send_error_to_support(e, "sspam_delay_input")


# Plugin Info
def get_info():
    return {
        "name": "Sticker Spam Plugin 🎭",
        "description": "Reply to a sticker with /sspam → confirm → enter delay → bot spams all stickers."
    }

async def test():
    return "✅ React plugin loaded successfully"


# Setup
def setup(app):
    app.add_handler(CommandHandler("sspam", sspam_command))
    app.add_handler(CallbackQueryHandler(sspam_buttons, pattern=r"^sspam_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sspam_delay_input))
