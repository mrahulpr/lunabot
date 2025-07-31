import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest
from plugins.db import db, send_error_to_support

MAX_WARNINGS = 3  # Change as needed

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    chat = update.effective_chat
    sender = update.effective_user
    message = update.message

    try:
        bot_member = await chat.get_member(bot.id)
        if not bot_member.can_restrict_members:
            return await message.reply_text("🚫 I need admin rights to warn users.")

        sender_member = await chat.get_member(sender.id)
        if sender_member.status not in ["administrator", "creator"]:
            return await message.reply_text("🛑 Only *admins* can use this command.", parse_mode="Markdown")

        target_user = None
        reason = "No reason provided"
        amount = 1

        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            if context.args:
                try:
                    amount = int(context.args[0])
                    reason = " ".join(context.args[1:]) or reason
                except ValueError:
                    reason = " ".join(context.args)
        elif context.args:
            user_arg = context.args[0]
            if user_arg.startswith("@"): user_arg = user_arg[1:]
            try:
                target_user = await bot.get_chat(user_arg)
                if len(context.args) >= 2:
                    try:
                        amount = int(context.args[1])
                        reason = " ".join(context.args[2:]) or reason
                    except ValueError:
                        reason = " ".join(context.args[1:])
            except Exception:
                return await message.reply_text("⚠️ Invalid username or ID provided.")
        else:
            return await message.reply_text("⚠️ Please reply to a user or provide a valid username or ID.")

        if target_user.id == bot.id:
            return await message.reply_text("🤖 I can't warn myself.")

        target_member = await chat.get_member(target_user.id)
        if target_member.status in ["administrator", "creator"]:
            return await message.reply_text("🛡️ Cannot warn an admin.")

        record = await db.warns.find_one({"chat_id": chat.id, "user_id": target_user.id})
        current_warns = record["count"] if record else 0
        new_count = current_warns + amount

        await db.warns.update_one(
            {"chat_id": chat.id, "user_id": target_user.id},
            {
                "$set": {
                    "username": target_user.username,
                    "full_name": target_user.full_name,
                    "last_warned": datetime.utcnow(),
                    "reason": reason,
                    "count": new_count,
                }
            },
            upsert=True,
        )

        if new_count >= MAX_WARNINGS:
            await bot.ban_chat_member(chat.id, target_user.id)
            await message.reply_text(
                f"🚫 *{target_user.full_name}* has been banned after reaching {MAX_WARNINGS} warnings.\n\nLast reason: {reason}",
                parse_mode="Markdown"
            )
        else:
            undo_token = f"{chat.id}:{target_user.id}:{datetime.utcnow().timestamp()}"
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Undo Warn", callback_data=f"undo_warn::{undo_token}")]
            ])

            sent = await message.reply_text(
                f"⚠️ *{target_user.full_name}* has been warned.\n\n*Reason:* {reason}\n*Warnings:* {new_count}/{MAX_WARNINGS}",
                reply_markup=buttons,
                parse_mode="Markdown"
            )

            await asyncio.sleep(60)

            try:
                await bot.edit_message_reply_markup(
                    chat_id=chat.id,
                    message_id=sent.message_id,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Warn added", callback_data="noop")]
                    ])
                )
                await db.warn_undo.delete_one({"undo_token": undo_token})
            except BadRequest:
                pass

    except Exception as e:
        import traceback
        await send_error_to_support(
            f"*❌ Error in warn plugin:*\n`{e}`\n```{traceback.format_exc()}```"
        )

async def undo_warn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        token = query.data.split("::", 1)[1]
        record = await db.warn_undo.find_one({"undo_token": token})

        if not record:
            return await query.answer("❌ Undo expired or invalid.", show_alert=True)

        if query.from_user.id != record["warned_by"]:
            return await query.answer("⚠️ Only the admin who warned can undo.", show_alert=True)

        await db.warns.update_one(
            {"chat_id": record["chat_id"], "user_id": record["user_id"]},
            {"$inc": {"count": -record["amount"]}}
        )

        await db.warn_undo.delete_one({"undo_token": token})

        await query.edit_message_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Warn undone", callback_data="noop")]])
        )
        await query.answer("✅ Warn undone.")

    except Exception as e:
        import traceback
        await send_error_to_support(
            f"*❌ Undo warn error:*\n`{e}`\n```{traceback.format_exc()}```"
        )

def get_info():
    return {
        "name": "Warn Plugin ⚠️",
        "description": "Warn users and auto-ban after a limit. Includes undo button for admins."
    }

async def test():
    assert db is not None, "MongoDB not connected"

def setup(app):
    app.add_handler(CommandHandler("warn", warn_user))
    app.add_handler(CallbackQueryHandler(undo_warn_callback, pattern=r"^undo_warn::"))
