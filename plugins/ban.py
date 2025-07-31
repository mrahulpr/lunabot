from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest
from plugins.db import db
from plugins.helpers import send_error_to_support
import traceback

async def resolve_user_argument(context: ContextTypes.DEFAULT_TYPE, chat_id: int, arg: str):
    bot = context.bot
    try:
        if arg.isdigit():
            return (await bot.get_chat_member(chat_id, int(arg))).user
        elif arg.startswith("@"):
            return await bot.get_chat(arg)
    except BadRequest:
        return None
    return None

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    chat = update.effective_chat
    sender = update.effective_user
    message = update.message

    try:
        bot_member = await chat.get_member(bot.id)
        if not bot_member.can_restrict_members:
            await message.reply_text("🚫 I can't ban users. Please make me an admin with ban rights.")
            return
    except BadRequest:
        await message.reply_text("🚫 I can't access member information. Please ensure I am an admin.")
        return

    sender_member = await chat.get_member(sender.id)
    if sender_member.status not in ["administrator", "creator"]:
        await message.reply_text("🛑 Only *admins* can use this command.", parse_mode="Markdown")
        return

    reason = "No reason provided."
    target_user = None

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        if context.args:
            reason = " ".join(context.args)
    elif context.args:
        user_arg = context.args[0]
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else reason
        target_user = await resolve_user_argument(context, chat.id, user_arg)

    if not target_user:
        await message.reply_text("⚠️ Please reply to a user or provide a valid @username or user ID to ban.")
        return

    if target_user.id == bot.id:
        await message.reply_text("I'm not going to ban myself. Silly human.")
        return

    target_member = await chat.get_member(target_user.id)
    if target_member.status in ["administrator", "creator"]:
        await message.reply_text("🛡️ I cannot ban an admin. Please demote them first.")
        return

    try:
        await bot.ban_chat_member(chat.id, target_user.id)
    except BadRequest as e:
        await message.reply_text(f"❌ Failed to ban user: {e.message}")
        return

    try:
        await db.bans.insert_one({
            "chat_id": chat.id,
            "user_id": target_user.id,
            "username": target_user.username,
            "full_name": target_user.full_name,
            "reason": reason
        })
    except Exception as e:
        await send_error_to_support(
            f"*❌ Database error in `ban_user`:*\n`{e}`\n```{traceback.format_exc()}```"
        )
        await message.reply_text(
            f"✅ *{target_user.full_name}* was banned, but failed to log to DB. Unban button may not work.",
            parse_mode="Markdown"
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔓 Unban", callback_data=f"unban::{chat.id}::{target_user.id}")]
    ])

    await message.reply_text(
        f"✅ *{target_user.full_name}* has been banned.\n📝 **Reason:** {reason}",
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
        await message.reply_text("🚫 I can't unban users. Please make me an admin with ban rights.")
        return

    sender_member = await chat.get_member(sender.id)
    if sender_member.status not in ["administrator", "creator"]:
        await message.reply_text("🛑 Only *admins* can use this command.", parse_mode="Markdown")
        return

    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif context.args:
        target_user = await resolve_user_argument(context, chat.id, context.args[0])

    if not target_user:
        await message.reply_text("⚠️ Please reply to a user or provide a valid @username or user ID to unban.")
        return

    try:
        await bot.unban_chat_member(chat.id, target_user.id)
    except BadRequest as e:
        await message.reply_text(f"❌ Failed to unban user: {e.message}")
        return

    try:
        await db.bans.update_many(
            {"chat_id": chat.id, "user_id": target_user.id},
            {"$set": {"reason": "[UNBANNED]"}}
        )
    except Exception as e:
        await send_error_to_support(
            f"*❌ DB error in `unban_user`:*\n`{e}`\n```{traceback.format_exc()}```"
        )
        await message.reply_text(
            f"✅ *{target_user.full_name}* has been unbanned, but DB update failed.",
            parse_mode="Markdown"
        )
        return

    await message.reply_text(f"✅ *{target_user.full_name}* has been unbanned.", parse_mode="Markdown")

async def unban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    bot = context.bot
    clicker = query.from_user

    try:
        _, chat_id_str, user_id_str = query.data.split("::")
        chat_id = int(chat_id_str)
        user_id = int(user_id_str)
    except (ValueError, IndexError):
        await query.answer("❗️ Invalid callback data.", show_alert=True)
        return

    try:
        member = await bot.get_chat_member(chat_id, clicker.id)
        if member.status not in ("administrator", "creator"):
            await query.answer("🛑 Only admins can use this button.", show_alert=True)
            return
    except BadRequest:
        await query.answer("❓ Could not verify your admin status.", show_alert=True)
        return

    try:
        record = await db.bans.find_one({
            "chat_id": chat_id,
            "user_id": user_id
        })
        if not record:
            await query.answer("✅ User already unbanned or record missing.", show_alert=True)
            await query.edit_message_text("This action was already completed.")
            return
    except Exception as e:
        await send_error_to_support(
            f"*❌ DB error in `unban_callback` (find):*\n`{e}`\n```{traceback.format_exc()}```"
        )
        await query.answer("Database error occurred.", show_alert=True)
        return

    try:
        await bot.unban_chat_member(chat_id, user_id)
        await db.bans.update_one(
            {"_id": record["_id"]},
            {"$set": {"reason": "[UNBANNED]"}}
        )
        await query.edit_message_text(
            f"✅ User unbanned by {clicker.mention_markdown()}.",
            parse_mode="Markdown"
        )
        await query.answer("Success!")
    except BadRequest as e:
        await query.edit_message_text(f"❌ Failed to unban: {e.message}")
    except Exception as e:
        await send_error_to_support(
            f"*❌ DB error in `unban_callback` (update):*\n`{e}`\n```{traceback.format_exc()}```"
        )
        await query.edit_message_text("✅ User unbanned, but database update failed.")

def get_info():
    return {
        "name": "Ban/Unban (MongoDB) 🔨",
        "description": "Ban users with reason and undo support. Uses MongoDB for logs."
    }

async def test():
    assert db is not None, "Database not initialized"

def setup(app):
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CallbackQueryHandler(unban_callback, pattern="^unban::"))
