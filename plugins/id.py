from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        chat_id = update.effective_chat.id
        return await update.message.reply_text(f"💬 This chat's ID: `{chat_id}`", parse_mode="Markdown")

    reply = update.message.reply_to_message

    if reply.forward_from_chat:
        # Forwarded from a channel or group
        origin = reply.forward_from_chat
        name = origin.title or origin.username or "Unknown"
        return await update.message.reply_text(
            f"📢 Forwarded from channel/group:\nName: `{name}`\nID: `{origin.id}`", parse_mode="Markdown"
        )

    if reply.forward_from:
        # Forwarded from a user
        user = reply.forward_from
        name = user.full_name or user.username or "Unknown"
        return await update.message.reply_text(
            f"👤 Forwarded from user:\nName: `{name}`\nID: `{user.id}`", parse_mode="Markdown"
        )

    if reply.from_user:
        # Replied to a user directly
        user = reply.from_user
        name = user.full_name or user.username or "Unknown"
        return await update.message.reply_text(
            f"👤 Replied to user:\nName: `{name}`\nID: `{user.id}`", parse_mode="Markdown"
        )

    # Fallback
    return await update.message.reply_text("⚠️ Couldn't extract any ID from the message.")

async def id_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "🆔 *ID Plugin*\n\n"
        "Get Telegram IDs from replies or chats.\n\n"
        "*Usage:*\n"
        "`/id` – Reply to a user or forwarded message to get their ID\\.\n"
        "If used without reply, it shows the current chat's ID\\."
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="help")]]
    await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=InlineKeyboardMarkup(keyboard))

def get_info():
    return {
        "name": "ID 🆔",
        "description": "Get Telegram user, group, channel, or chat ID. Works on replies or directly in chat."
    }

def setup(app):
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CallbackQueryHandler(id_help_callback, pattern="^plugin::id$"))
