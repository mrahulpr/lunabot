# plugin/ban.py
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest
from plugins.db import db  # MongoDB connection

# Define a timeout for the "undo" unban button
UNBAN_TIMEOUT = timedelta(minutes=1)

async def resolve_user_argument(context: ContextTypes.DEFAULT_TYPE, chat_id: int, arg: str):
    """Resolves a user from a user ID or @username."""
    bot = context.bot
    try:
        if arg.isdigit():
            return (await bot.get_chat_member(chat_id, int(arg))).user
        elif arg.startswith("@"):
            return await bot.get_chat(arg)
    except BadRequest: # <<< FIX: More specific exception
        return None
    return None

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bans a user from the chat."""
    bot = context.bot
    chat = update.effective_chat
    sender = update.effective_user
    message = update.message

    # Check if the bot has admin rights to ban
    try:
        bot_member = await chat.get_member(bot.id)
        if not bot_member.can_restrict_members:
            await message.reply_text("🚫 I can't ban users. Please make me an admin with ban rights.")
            return
    except BadRequest:
        await message.reply_text("🚫 I can't access member information. Please ensure I am an admin.")
        return

    # Check if the command issuer is an admin
    sender_member = await chat.get_member(sender.id)
    if sender_member.status not in ["administrator", "creator"]:
        await message.reply_text("🛑 Only *admins* can use this command.", parse_mode="Markdown")
        return

    reason = "No reason provided."
    target_user = None

    # Determine the target user (from reply or argument)
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

    # <<< FIX: Check if the target user is an admin or the bot itself
    if target_user.id == bot.id:
        await message.reply_text("I'm not going to ban myself. Silly human.")
        return

    target_member = await chat.get_member(target_user.id)
    if target_member.status in ["administrator", "creator"]:
        await message.reply_text("🛡️ I cannot ban an admin. Please demote them first.")
        return
    # <<< END FIX

    # Ban the user
    try:
        await bot.ban_chat_member(chat.id, target_user.id)
    except BadRequest as e:
        await message.reply_text(f"❌ Failed to ban user: {e.message}")
        return

    # <<< FIX: Wrap database operation in a try...except block
    try:
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
    except Exception as e:
        print(f"DATABASE ERROR in ban_user: {e}")
        await message.reply_text(
            f"✅ *{target_user.full_name}* was banned, but I failed to log it to the database. The unban button will not work.",
            parse_mode="Markdown"
        )
        return
    # <<< END FIX

    # Send confirmation with an inline "unban" button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔓 Unban ({int(UNBAN_TIMEOUT.total_seconds())}s)", callback_data=f"unban::{chat.id}::{target_user.id}")]
    ])

    await message.reply_text(
        f"✅ *{target_user.full_name}* has been banned.\n📝 **Reason:** {reason}",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unbans a user from the chat via command."""
    bot = context.bot
    chat = update.effective_chat
    sender = update.effective_user
    message = update.message

    # Check bot and user permissions
    bot_member = await chat.get_member(bot.id)
    if not bot_member.can_restrict_members:
        await message.reply_text("🚫 I can't unban users. Please make me an admin with ban rights.")
        return

    sender_member = await chat.get_member(sender.id)
    if sender_member.status not in ["administrator", "creator"]:
        await message.reply_text("🛑 Only *admins* can use this command.", parse_mode="Markdown")
        return

    # Determine the target user
    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif context.args:
        target_user = await resolve_user_argument(context, chat.id, context.args[0])

    if not target_user:
        await message.reply_text("⚠️ Please reply to a user or provide a valid @username or user ID to unban.")
        return

    # Unban the user
    try:
        await bot.unban_chat_member(chat.id, target_user.id)
    except BadRequest as e:
        await message.reply_text(f"❌ Failed to unban user: {e.message}")
        return

    # <<< FIX: Wrap database operation in a try...except block
    try:
        await db.bans.update_many(
            {"chat_id": chat.id, "user_id": target_user.id, "unbanned": False},
            {"$set": {"unbanned": True, "unbanned_by": sender.id, "unbanned_at": datetime.utcnow()}}
        )
    except Exception as e:
        print(f"DATABASE ERROR in unban_user: {e}")
        await message.reply_text(f"✅ *{target_user.full_name}* has been unbanned, but I failed to update my database records.")
        return
    # <<< END FIX

    await message.reply_text(f"✅ *{target_user.full_name}* has been unbanned.", parse_mode="Markdown")

async def unban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the inline 'unban' button press."""
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

    # <<< FIX: Check if the user clicking the button is an admin
    try:
        member = await bot.get_chat_member(chat_id, clicker.id)
        if member.status not in ("administrator", "creator"):
            await query.answer("🛑 Only admins can use this button.", show_alert=True)
            return
    except BadRequest:
        await query.answer("❓ Could not verify your admin status.", show_alert=True)
        return
    # <<< END FIX

    # <<< FIX: Safer check for expiry and record existence
    try:
        record = await db.bans.find_one({
            "chat_id": chat_id,
            "user_id": user_id,
            "unbanned": False
        })
        if not record:
            await query.answer("✅ User is already unbanned or the record is missing.", show_alert=True)
            await query.edit_message_text("This action has already been completed.")
            return

        expiry_time = record.get("unban_token_expire")
        if not expiry_time or datetime.utcnow() > expiry_time:
            await query.answer("⌛️ The time to undo this ban has expired.", show_alert=True)
            await query.edit_message_text(f"Ban time for user {user_id} has expired.")
            return
    except Exception as e:
        print(f"DATABASE ERROR in unban_callback (find): {e}")
        await query.answer("A database error occurred.", show_alert=True)
        return
    # <<< END FIX

    # Unban the user via API and update the database
    try:
        await bot.unban_chat_member(chat_id, user_id)
        await db.bans.update_one(
            {"_id": record["_id"]}, # Use the specific record ID for update
            {"$set": {"unbanned": True, "unbanned_by": clicker.id, "unbanned_at": datetime.utcnow()}}
        )
        await query.edit_message_text(f"✅ User unbanned by {clicker.mention_markdown()}.", parse_mode="Markdown")
        await query.answer("Success!")
    except BadRequest as e:
        await query.edit_message_text(f"❌ Failed to unban: {e.message}")
    except Exception as e:
        print(f"DATABASE ERROR in unban_callback (update): {e}")
        await query.edit_message_text("✅ User was unbanned, but a database error occurred.")

def get_info():
    """Returns plugin info."""
    return {
        "name": "Ban/Unban (MongoDB) 🔨",
        "description": "Ban users with reason and undo with persistent log support."
    }

async def test():
    # Basic plugin health check
    assert db is not None, "Database not initialized"


def setup(app):
    """Sets up the command and callback handlers."""
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CallbackQueryHandler(unban_callback, pattern="^unban::"))
