from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from openai import AsyncOpenAI
from plugins.db import db, send_error_to_support
from datetime import datetime
import os
import traceback

# Load your ChatGPT API key from secrets or env
import os
from openai import AsyncOpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Settings collection
SETTINGS = db.chatgpt_settings

async def chatgpt_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat
        is_admin = False
        if chat.type != "private":
            member = await chat.get_member(user.id)
            is_admin = member.status in ["administrator", "creator"]

        doc = await SETTINGS.find_one({"chat_id": chat.id}) or {}

        enabled_users = set(doc.get("enabled_users", []))
        group_enabled = doc.get("group_enabled", False)

        buttons = [
            [
                InlineKeyboardButton(
                    f"{'✅ ' if user.id in enabled_users else ''}Enable for me only",
                    callback_data="chatgpt_toggle_user"
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if group_enabled else ''}Enable in group for all",
                    callback_data="chatgpt_toggle_group"
                ) if is_admin else None
            ]
        ]

        # Remove None buttons
        buttons = [[b for b in row if b] for row in buttons if any(row)]

        await update.message.reply_text(
            "⚙️ *ChatGPT Settings*\n\n"
            "• Use the buttons below to toggle ChatGPT replies.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await send_error_to_support(f"chatgpt_toggle error:\n`{traceback.format_exc()}`")

async def chatgpt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user = query.from_user
        chat = update.effective_chat

        doc = await SETTINGS.find_one({"chat_id": chat.id}) or {}
        enabled_users = set(doc.get("enabled_users", []))
        group_enabled = doc.get("group_enabled", False)

        if query.data == "chatgpt_toggle_user":
            if user.id in enabled_users:
                enabled_users.remove(user.id)
            else:
                enabled_users.add(user.id)
            await SETTINGS.update_one(
                {"chat_id": chat.id},
                {"$set": {"enabled_users": list(enabled_users)}},
                upsert=True
            )

        elif query.data == "chatgpt_toggle_group":
            member = await chat.get_member(user.id)
            if member.status not in ["administrator", "creator"]:
                await query.answer("Only admins can toggle this.", show_alert=True)
                return
            group_enabled = not group_enabled
            await SETTINGS.update_one(
                {"chat_id": chat.id},
                {"$set": {"group_enabled": group_enabled}},
                upsert=True
            )

        # Refresh buttons
        new_doc = await SETTINGS.find_one({"chat_id": chat.id}) or {}
        new_enabled_users = set(new_doc.get("enabled_users", []))
        new_group_enabled = new_doc.get("group_enabled", False)

        buttons = [
            [
                InlineKeyboardButton(
                    f"{'✅ ' if user.id in new_enabled_users else ''}Enable for me only",
                    callback_data="chatgpt_toggle_user"
                ),
                InlineKeyboardButton(
                    f"{'✅ ' if new_group_enabled else ''}Enable in group for all",
                    callback_data="chatgpt_toggle_group"
                ) if await is_admin(context, chat.id, user.id) else None
            ]
        ]
        buttons = [[b for b in row if b] for row in buttons if any(row)]

        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        await send_error_to_support(f"chatgpt_callback error:\n`{traceback.format_exc()}`")

async def is_admin(context, chat_id, user_id):
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

async def chatgpt_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.effective_chat or not update.effective_user:
            return

        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        text = update.message.text
        if not text or text.startswith("/"):
            return

        doc = await SETTINGS.find_one({"chat_id": chat_id}) or {}
        enabled_users = doc.get("enabled_users", [])
        group_enabled = doc.get("group_enabled", False)

        allow = False
        if user_id in enabled_users:
            allow = True
        elif group_enabled:
            allow = True

        if not allow:
            return

        # Call OpenAI
        res = await openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text}]
        )
        reply = res.choices[0].message.content

        await update.message.reply_text(f"```\n{reply}\n```", parse_mode="Markdown")
    except Exception as e:
        await send_error_to_support(f"chatgpt_reply error:\n`{traceback.format_exc()}`")

def setup(app):
    app.add_handler(CommandHandler("chatgpt", chatgpt_toggle))
    app.add_handler(CallbackQueryHandler(chatgpt_callback, pattern="^chatgpt_toggle_"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chatgpt_reply))

def get_info():
    return {
        "name": "ChatGPT Plugin 🤖",
        "description": "ChatGPT replies to messages when enabled by user or admin."
    }

async def test():
    assert OPENAI_API_KEY, "ChatGPT API key not set"
    assert db is not None, "MongoDB not connected"
