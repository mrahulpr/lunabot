import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest
from plugins.db import db, send_error_to_support

DEFAULT_DURATION = 60 * 60  # 1 hour in seconds

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        chat = update.effective_chat
        bot = context.bot
        sender = update.effective_user

        # Check permissions
        bot_member = await chat.get_member(bot.id)
        if not bot_member.can_restrict_members:
            return await message.reply_text("🚫 I need permission to restrict members.")
        
        sender_member = await chat.get_member(sender.id)
        if sender_member.status not in ["administrator", "creator"]:
            return await message.reply_text("🛑 Only *admins* can use this command.", parse_mode="Markdown")

        # Parse target user
        reason = "No reason provided."
        duration = DEFAULT_DURATION
        target_user = None

        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            if context.args:
                duration, reason = parse_args(context.args)
        elif context.args:
            user_arg = context.args[0]
            duration, reason = parse_args(context.args[1:])
            if user_arg.startswith("@"):
                user_arg = user_arg[1:]
            try:
                target_user = await bot.get_chat(user_arg)
            except Exception:
                pass

        if not target_user:
            return await message.reply_text("⚠️ Please reply to a user or provide a valid @username or ID.")

        if target_user.id == bot.id:
            return await message.reply_text("🤖 I can’t mute myself.")

        target_member = await chat.get_member(target_user.id)
        if target_member.status in ["administrator", "creator"]:
            return await message.reply_text("🛡️ Cannot mute an admin.")

        until = datetime.utcnow() + timedelta(seconds=duration)

        await bot.restrict_chat_member(
            chat.id,
            target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until,
        )

        await db.mutes.insert_one({
            "chat_id": chat.id,
            "user_id": target_user.id,
            "muted_by": sender.id,
            "until": until,
            "reason": reason,
            "timestamp": datetime.utcnow(),
        })

        # Inline undo button
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 Undo Mute", callback_data=f"undo_mute:{chat.id}:{target_user.id}")
        ]])

        sent = await message.reply_text(
            f"🔇 *{target_user.full_name}* has been muted for *{duration//60} minutes*.\n\n*Reason:* {reason}",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        await asyncio.sleep(60)
        try:
            await sent.edit_reply_markup(
                InlineKeyboardMarkup([[
                    InlineKeyboardButton("Muted ✅", callback_data="noop")
                ]])
            )
        except Exception:
            pass

    except Exception as e:
        import traceback
        await send_error_to_support(
            f"*❌ Mute Error:*\n`{e}`\n```{traceback.format_exc()}```"
        )

async def undo_mute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        parts = query.data.split(":")
        chat_id = int(parts[1])
        user_id = int(parts[2])

        await context.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=True)
        )

        await db.mutes.delete_many({"chat_id": chat_id, "user_id": user_id})
        await query.edit_message_text("✅ Mute undone successfully.")

    except Exception as e:
        import traceback
        await send_error_to_support(
            f"*❌ Undo Mute Error:*\n`{e}`\n```{traceback.format_exc()}```"
        )

def parse_args(args):
    """
    Parses duration and reason. Returns (seconds, reason_str).
    Example: ['10m', 'Spamming'] => (600, "Spamming")
    """
    duration = DEFAULT_DURATION
    reason = "No reason provided."
    if args:
        dur_str = args[0]
        if dur_str.endswith("m"):
            duration = int(dur_str[:-1]) * 60
        elif dur_str.endswith("h"):
            duration = int(dur_str[:-1]) * 3600
        elif dur_str.endswith("d"):
            duration = int(dur_str[:-1]) * 86400
        else:
            reason = " ".join(args)
            return duration, reason
        if len(args) > 1:
            reason = " ".join(args[1:])
    return duration, reason

def get_info():
    return {
        "name": "Mute 🔇",
        "description": "Temporarily mute a user. Admins only."
    }

async def test():
    assert db is not None, "MongoDB not connected"

def setup(app):
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CallbackQueryHandler(undo_mute_callback, pattern="^undo_mute:"))
