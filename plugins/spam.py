import os
import traceback
import asyncio
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, Sticker
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from plugins.db import db

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")

# --- States ---
WAITING_DELAY = 1

# --- Error logging ---
async def send_error_to_support(error: Exception, where="sspam_plugin"):
    if not BOT_TOKEN or not SUPPORT_CHAT_ID:
        return
    bot = Bot(BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=(f"❗️ *Plugin Error: {where}*\n"
                  f"`{str(error)}`\n\n"
                  f"```{traceback.format_exc()}```")[:4000],
            parse_mode="MarkdownV2"
        )
    except Exception:
        pass

# --- Start command ---
async def sspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.reply_to_message or not update.message.reply_to_message.sticker:
            await update.message.reply_text("⚠️ Reply to a sticker with /sspam to use this command.")
            return ConversationHandler.END

        sticker: Sticker = update.message.reply_to_message.sticker
        set_name = sticker.set_name
        if not set_name:
            await update.message.reply_text("⚠️ This sticker is not from a sticker pack.")
            return ConversationHandler.END

        # Save info
        context.user_data["sspam_set"] = set_name
        context.user_data["sspam_chat"] = update.effective_chat.id
        context.user_data["sspam_user"] = update.effective_user.id

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("▶️ Start", callback_data="sspam_start"),
            InlineKeyboardButton("❌ Cancel", callback_data="sspam_cancel")
        ]])

        await update.message.reply_text(
            f"🎭 Sticker Spam ready for pack: `{set_name}`\n\nChoose an option:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return WAITING_DELAY

    except Exception as e:
        await send_error_to_support(e, "sspam_command")
        return ConversationHandler.END

# --- Handle buttons ---
async def sspam_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        if query.data == "sspam_cancel":
            await query.edit_message_text("❌ Spam cancelled.")
            return ConversationHandler.END

        if query.data == "sspam_start":
            await query.edit_message_text("⏳ Send me the delay (in seconds) between stickers:")
            return WAITING_DELAY

    except Exception as e:
        await send_error_to_support(e, "sspam_button")
        return ConversationHandler.END

# --- Handle delay input ---
async def sspam_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = context.user_data.get("sspam_user")
        chat_id = context.user_data.get("sspam_chat")

        if update.effective_user.id != user_id or update.effective_chat.id != chat_id:
            return  # ignore others

        try:
            delay = float(update.message.text.strip())
            if delay <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⚠️ Please send a valid positive number (seconds).")
            return WAITING_DELAY

        try:
            await update.message.delete()
        except Exception:
            pass

        set_name = context.user_data.get("sspam_set")
        if not set_name:
            await update.message.reply_text("⚠️ Sticker pack missing. Please try again.")
            return ConversationHandler.END

        bot: Bot = context.bot
        stickers = await bot.get_sticker_set(set_name)
        await bot.send_message(chat_id, f"🚀 Starting spam with {delay} sec delay ({len(stickers.stickers)} stickers)…")

        for stk in stickers.stickers:
            try:
                await bot.send_sticker(chat_id, stk.file_id)
                await asyncio.sleep(delay)
            except Exception:
                continue

        await bot.send_message(chat_id, "✅ Sticker spam completed.")
        return ConversationHandler.END

    except Exception as e:
        await send_error_to_support(e, "sspam_delay")
        return ConversationHandler.END

# --- Cancel handler ---
async def sspam_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Spam cancelled.")
    return ConversationHandler.END

# --- Plugin Info ---
def get_info():
    return {
        "name": "Sticker Spam 🎭",
        "description": "Reply to a sticker with /sspam, confirm via button, then spam the whole pack."
    }

# --- Setup ---
def setup(app):
    conv = ConversationHandler(
        entry_points=[CommandHandler("sspam", sspam)],
        states={
            WAITING_DELAY: [
                CallbackQueryHandler(sspam_button, pattern="^sspam_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, sspam_delay)
            ]
        },
        fallbacks=[CommandHandler("cancel", sspam_cancel)],
        name="sspam_conv",
        persistent=False,
        per_message=True  # Important to avoid blocking other handlers
    )
    app.add_handler(conv)

# --- Test ---
async def test():
    return "✅ Sticker spam plugin loaded successfully"
