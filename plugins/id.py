import os
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")


async def send_error_to_support(error: Exception, where="id_plugin"):
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


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.reply_to_message:
            chat_id = update.effective_chat.id
            return await update.message.reply_text(
                f"💬 This chat's ID: `{chat_id}`",
                parse_mode="MarkdownV2"
            )

        reply = update.message.reply_to_message

        if reply.forward_from_chat:
            origin = reply.forward_from_chat
            name = origin.title or origin.username or "Unknown"
            return await update.message.reply_text(
                f"📢 Forwarded from channel/group:\nName: `{name}`\nID: `{origin.id}`",
                parse_mode="MarkdownV2"
            )

        if reply.forward_from:
            user = reply.forward_from
            name = user.full_name or user.username or "Unknown"
            return await update.message.reply_text(
                f"👤 Forwarded from user:\nName: `{name}`\nID: `{user.id}`",
                parse_mode="MarkdownV2"
            )

        if reply.from_user:
            user = reply.from_user
            name = user.full_name or user.username or "Unknown"
            return await update.message.reply_text(
                f"👤 Replied to user:\nName: `{name}`\nID: `{user.id}`",
                parse_mode="MarkdownV2"
            )

        return await update.message.reply_text(
            "⚠️ Couldn't extract any ID from the message.",
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        await send_error_to_support(e, "get_id")


async def id_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        text = (
            "🆔 *ID Plugin*\n\n"
            "Get Telegram IDs from replies or chats\\.\n\n"
            "*Usage:*\n"
            "`/id` – Reply to a user or forwarded message to get their ID\\.\n"
            "If used without reply, it shows the current chat's ID\\."
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="help")]]
        await query.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await send_error_to_support(e, "id_help_callback")


def get_info():
    return {
        "name": "ID 🆔",
        "description": "Get Telegram user, group, channel, or chat ID. Works on replies or forwarded messages."
    }


def setup(app):
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CallbackQueryHandler(id_help_callback, pattern="^plugin::id$"))
