from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest
from plugins.db import db, send_error_to_support
import asyncio

MUTE_DURATION = 60 * 60  # 1 hour mute

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        bot = context.bot
        chat = update.effective_chat
        sender = update.effective_user
        message = update.message

        # Bot permissions
        bot_member = await chat.get_member(bot.id)
        if not bot_member.can_restrict_members:
            return await message.reply_text("🚫 I need permission to restrict users.")

        # Admin check
        sender_member = await chat.get_member(sender.id)
        if sender_member.status not in ["administrator", "creator"]:
            return await message.reply_text("🛑 Only *admins* can use this command.", parse_mode="Markdown")

        # Target user
        if not message.reply_to_message:
            return await message.reply_text("⚠️ Reply to a user to mute them.")

        target = message.reply_to_message.from_user
        if target.id == bot.id:
            return await message.reply_text("🤖 I can't mute myself.")
        if target.id == sender.id:
            return await message.reply_text("🙃 You can't mute yourself.")
        target_member = await chat.get_member(target.id)
        if target_member.status in ["administrator", "creator"]:
            return await message.reply_text("🛡️ Cannot mute an admin.")

        # Reason
        reason = " ".join(context.args) if context.args else "No reason provided."

        # Apply mute
        until = datetime.utcnow() + timedelta(seconds=MUTE_DURATION)
        await bot.restrict_chat_member(
            chat.id,
            target.id,
            permissions=ChatPermissions(),
            until_date=until
        )

        # Store in DB
        await db.mutes.insert_one({
            "chat_id": chat.id,
            "user_id": target.id,
            "muted_by": sender.id,
            "muted_at": datetime.utcnow(),
            "until": until,
            "reason": reason
        })

        # Undo button
        undo_data = f"mute_undo:{chat.id}:{target.id}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Undo Mute", callback_data=undo_data)]
        ])
        msg = await message.reply_text(
            f"🔇 *{target.full_name}* has been muted for 1 hour.\n\n*Reason:* {reason}",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        # After 1 minute, edit the button
        await asyncio.sleep(60)
        try:
            await msg.edit_reply_markup(
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Mute added", callback_data="noop")]
                ])
            )
        except BadRequest:
            pass

    except Exception as e:
        import traceback
        await send_error_to_support(f"*❌ Mute Error:*\n`{e}`\n```{traceback.format_exc()}```")


async def undo_mute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user = query.from_user
        parts = query.data.split(":")
        chat_id = int(parts[1])
        target_user_id = int(parts[2])

        # Check if the user is admin
        member = await context.bot.get_chat_member(chat_id, user.id)
        if member.status not in ["administrator", "creator"]:
            return await query.answer("❌ Only admins can undo mute.", show_alert=True)

        # Unmute the user
        await context.bot.restrict_chat_member(
            chat_id,
            target_user_id,
            permissions=ChatPermissions(can_send_messages=True)
        )

        await db.mutes.delete_many({"chat_id": chat_id, "user_id": target_user_id})
        await query.edit_message_text("✅ Mute undone successfully.")

    except Exception as e:
        import traceback
        await send_error_to_support(f"*❌ Undo Mute Error:*\n`{e}`\n```{traceback.format_exc()}```")


def get_info():
    return {
        "name": "Mute 🔇",
        "description": "Mutes a user for 1 hour. Admins only. Includes undo option."
    }

async def test():
    assert db is not None, "DB not connected"

def setup(app):
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CallbackQueryHandler(undo_mute_callback, pattern="^mute_undo:"))
