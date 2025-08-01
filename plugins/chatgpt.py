import os
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from openai import AsyncOpenAI
from plugins.db import db, send_error_to_support

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai = AsyncOpenAI(api_key=OPENAI_API_KEY)
SETTINGS = db.chatgpt_settings

# --- Admin Check ---
async def is_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except Exception:
        return False

# --- /chatgpt command ---
async def chatgpt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat
        doc = await SETTINGS.find_one({"chat_id": chat.id}) or {}
        enabled_users = doc.get("enabled_users", [])
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
                ) if await is_admin(context, chat.id, user.id) else None
            ]
        ]
        buttons = [[b for b in row if b] for row in buttons if any(row)]
        await update.message.reply_text(
            "ChatGPT toggle options:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception:
        await send_error_to_support(traceback.format_exc())

# --- Callback buttons handler ---
async def chatgpt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user = query.from_user
        chat = query.message.chat
        data = query.data

        doc = await SETTINGS.find_one({"chat_id": chat.id}) or {}
        enabled_users = doc.get("enabled_users", [])
        group_enabled = doc.get("group_enabled", False)

        if data == "chatgpt_toggle_user":
            if user.id in enabled_users:
                enabled_users.remove(user.id)
                await query.answer("❌ Disabled for you")
            else:
                enabled_users.append(user.id)
                await query.answer("✅ Enabled for you")
            await SETTINGS.update_one({"chat_id": chat.id}, {"$set": {"enabled_users": enabled_users}}, upsert=True)

        elif data == "chatgpt_toggle_group":
            if not await is_admin(context, chat.id, user.id):
                await query.answer("Only admins can toggle this.", show_alert=True)
                return
            group_enabled = not group_enabled
            await SETTINGS.update_one({"chat_id": chat.id}, {"$set": {"group_enabled": group_enabled}}, upsert=True)
            await query.answer("✅ Group setting toggled")

        new_doc = await SETTINGS.find_one({"chat_id": chat.id}) or {}
        new_enabled_users = new_doc.get("enabled_users", [])
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
    except Exception:
        await send_error_to_support(traceback.format_exc())

# --- Auto reply handler ---
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

        if user_id not in enabled_users and not group_enabled:
            return

        res = await openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text}]
        )
        reply = res.choices[0].message.content.strip()
        await update.message.reply_text(f"```\n{reply}\n```", parse_mode="Markdown")
    except Exception:
        await send_error_to_support(traceback.format_exc())

# --- Setup ---
def setup(app):
    app.add_handler(CommandHandler("chatgpt", chatgpt_command))
    app.add_handler(CallbackQueryHandler(chatgpt_callback, pattern="^chatgpt_toggle_"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chatgpt_reply))

def get_info():
    return {
        "name": "ChatGPT Plugin",
        "description": "ChatGPT replies to messages when enabled by user or admin."
    }

async def test():
    assert OPENAI_API_KEY, "ChatGPT API key not set"
    await db.command("ping")
