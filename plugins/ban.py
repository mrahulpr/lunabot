# plugin/ban.py
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from plugin.db import db  # MongoDB connection

UNBAN_TIMEOUT = timedelta(minutes=1)

async def resolve_user_argument(context: ContextTypes.DEFAULT_TYPE, chat_id: int, arg: str):
    bot = context.bot
    try:
        if arg.isdigit():
            return (await bot.get_chat_member(chat_id, int(arg))).user
        elif arg.startswith("@"):
            return await bot.get_chat(arg)
    except Exception:
        return None
    return None

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    chat = update.effective_chat
    sender = update.effective_user
    message = update.message

    bot_member = await chat.get_member(bot.id)
    if not bot_member.can_restrict_members:
        return await message.reply_text("🚫 I can't ban users. Please make me admin with ban rights.")

    sender_member = await chat.get_member(sender.id)
    if sender_member.status not in ["administrator", "creator"]:
        return await message.reply_text("🛑 Only *admins* can ban users.", parse_mode="Markdown")

    reason = "No reason provided."
    target_user = None

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        reason = " ".join(context.args) if context.args else reason
    elif context.args:
        user_arg = context.args[0]
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else reason
        target_user = await resolve_user_argument(context, chat.id, user_arg)

    if not target_user:
        return await message.reply_text("⚠️ Couldn't resolve user. Reply or use a valid @username or ID.")

    try:
        await bot.ban_chat_member(chat.id, target_user.id)
    except Exception as e:
        return await message.reply_text(f"❌ Failed to ban user: {e}")

    # Save ban to DB
    await db.bans.insert_one({
        "chat_id": chat.id,
        "user_id": target_user.id,
        "username": target_user.username,
        "full_name": target_user.full_name,
        "reason": reason,
        "banned_by": sender.id,
        "banned_at": datetime.utcnow(),
        "unbanned": False,
        "unban_token_expire": datetime.utcnow() + UNBAN_TIMEOUT
    })

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔓 Unban (1 min)", callback_data=f"unban::{chat.id}::{target_user.id}")]
    ])

    await message.reply_text(
        f"✅ *{target_user.full_name}* was banned.\n📝 Reason: {reason}",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    chat = update.effective_chat
    sender = update.effective_user
    message = update.message

    bot_member = await chat.get_member(bot.id)
    if not bot_member.can_restrict_members:
        return await message.reply_text("🚫 I can't unban users. Please make me admin with unban rights.")

    sender_member = await chat.get_member(sender.id)
    if sender_member.status not in ["administrator", "creator"]:
        return await message.reply_text("🛑 Only *admins* can unban users.", parse_mode="Markdown")

    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif context.args:
        target_user = await resolve_user_argument(context, chat.id, context.args[0])

    if not target_user:
        return await message.reply_text("⚠️ Couldn't resolve user. Reply or use a valid @username or ID.")

    try:
        await bot.unban_chat_member(chat.id, target_user.id)
    except Exception as e:
        return await message.reply_text(f"❌ Failed to unban user: {e}")

    await db.bans.update_many(
        {"chat_id": chat.id, "user_id": target_user.id, "unbanned": False},
        {"$set": {"unbanned": True, "unbanned_by": sender.id, "unbanned_at": datetime.utcnow()}}
    )

    await message.reply_text(f"✅ *{target_user.full_name}* has been unbanned.", parse_mode="Markdown")

async def unban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    bot = context.bot

    try:
        _, chat_id, user_id = query.data.split("::")
        chat_id = int(chat_id)
        user_id = int(user_id)
    except:
        return await query.answer("❗ Invalid unban callback data.", show_alert=True)

    now = datetime.utcnow()
    record = await db.bans.find_one({
        "chat_id": chat_id,
        "user_id": user_id,
        "unbanned": False
    })

    if not record or now > record["unban_token_expire"]:
        return await query.answer("⌛ Unban period expired or already unbanned.", show_alert=True)

    try:
        await bot.unban_chat_member(chat_id, user_id)
        await db.bans.update_many(
            {"chat_id": chat_id, "user_id": user_id, "unbanned": False},
            {"$set": {"unbanned": True, "unbanned_by": query.from_user.id, "unbanned_at": now}}
        )
        await query.edit_message_text("✅ User has been unbanned.")
    except Exception as e:
        await query.edit_message_text(f"❌ Failed to unban: {e}")

def get_info():
    return {
        "name": "Ban/Unban (MongoDB) 🔨",
        "description": "Ban users with reason and undo with persistent log support."
    }

def setup(app):
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CallbackQueryHandler(unban_callback, pattern="^unban::"))
