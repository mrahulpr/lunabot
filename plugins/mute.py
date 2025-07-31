import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ChatPermissions
from plugins.db import db, send_error_to_support

DEFAULT_DURATION = 60 * 60  # 1 hour in seconds

def parse_duration(input_str):
    try:
        num = int(input_str[:-1])
        unit = input_str[-1].lower()
        if unit == 'm':
            return num * 60
        elif unit == 'h':
            return num * 60 * 60
        elif unit == 'd':
            return num * 24 * 60 * 60
    except Exception:
        pass
    return None

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        bot = context.bot
        chat = update.effective_chat
        admin = update.effective_user

        if not message.reply_to_message:
            return await message.reply_text("⚠️ You must reply to a user's message to mute them.")

        user = message.reply_to_message.from_user

        bot_member = await chat.get_member(bot.id)
        if not bot_member.can_restrict_members:
            return await message.reply_text("🚫 I need permission to restrict users.")

        admin_member = await chat.get_member(admin.id)
        if admin_member.status not in ["administrator", "creator"]:
            return await message.reply_text("🛑 Only admins can use this command.")

        if user.id == bot.id:
            return await message.reply_text("🤖 I can't mute myself.")
        if user.id == int(context.bot_data.get("OWNER_ID", 0)):
            return await message.reply_text("🛡️ I won't mute my owner.")
        target_member = await chat.get_member(user.id)
        if target_member.status in ["administrator", "creator"]:
            return await message.reply_text("🛡️ I can't mute admins.")

        args = context.args
        duration = DEFAULT_DURATION
        reason = "No reason provided."

        if args:
            custom_duration = parse_duration(args[0])
            if custom_duration:
                duration = custom_duration
                reason = " ".join(args[1:]) if len(args) > 1 else reason
            else:
                reason = " ".join(args)

        until_date = datetime.utcnow() + timedelta(seconds=duration)

        await bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )

        # Save mute record
        await db.mutes.update_one(
            {"chat_id": chat.id, "user_id": user.id},
            {
                "$set": {
                    "username": user.username,
                    "full_name": user.full_name,
                    "muted_at": datetime.utcnow(),
                    "reason": reason,
                    "duration": duration
                }
            },
            upsert=True
        )

        msg = await message.reply_text(
            f"🔇 *{user.full_name}* has been muted for *{int(duration // 60)} minutes*.\n*Reason:* {reason}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🚫 Undo Mute", callback_data=f"unmute::{chat.id}::{user.id}")]]
            )
        )

        await asyncio.sleep(60)
        try:
            await msg.edit_reply_markup(
                InlineKeyboardMarkup([[InlineKeyboardButton("✅ Muted", callback_data="muted_done")]])
            )
        except:
            pass

    except Exception as e:
        import traceback
        await send_error_to_support(f"*❌ Mute error:*\n`{e}`\n```{traceback.format_exc()}```")

async def unmute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        data = query.data.split("::")
        if len(data) != 3:
            return

        chat_id = int(data[1])
        user_id = int(data[2])
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=True)
        )

        await db.mutes.delete_one({"chat_id": chat_id, "user_id": user_id})

        await query.edit_message_text("✅ User has been unmuted.")
    except Exception as e:
        import traceback
        await send_error_to_support(f"*❌ Unmute error:*\n`{e}`\n```{traceback.format_exc()}```")

def get_info():
    return {
        "name": "Mute Plugin 🔇",
        "description": "Mute users temporarily with optional duration and undo support."
    }

async def test():
    assert db is not None, "MongoDB not connected"

def setup(app):
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CallbackQueryHandler(unmute_callback, pattern="^unmute::"))
