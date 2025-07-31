from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from openai import AsyncOpenAI
from core.db import db
from plugins.helpers import send_error_to_support
import os
import traceback

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def chatgpt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyboard = [
            [
                InlineKeyboardButton("🧠 Enable for me only", callback_data="chatgpt:user"),
                InlineKeyboardButton("🌍 Enable in group for all", callback_data="chatgpt:group"),
            ]
        ]
        await update.message.reply_text(
            "Enable ChatGPT reply mode:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        await send_error_to_support(traceback.format_exc())


async def handle_chatgpt_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        data = query.data.split(":")[1]

        if data == "user":
            entry = await db.chatgpt_users.find_one({"user_id": user_id})
            if entry:
                await db.chatgpt_users.delete_one({"user_id": user_id})
                await query.answer("❌ Disabled for you")
            else:
                await db.chatgpt_users.insert_one({"user_id": user_id})
                await query.answer("✅ Enabled for you")

        elif data == "group":
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status not in ["creator", "administrator"]:
                await query.answer("Only admins can enable group-wide ChatGPT.", show_alert=True)
                return

            entry = await db.chatgpt_groups.find_one({"chat_id": chat_id})
            if entry:
                await db.chatgpt_groups.delete_one({"chat_id": chat_id})
                await query.answer("❌ Disabled for this group")
            else:
                await db.chatgpt_groups.insert_one({"chat_id": chat_id})
                await query.answer("✅ Enabled for this group")

    except Exception:
        await send_error_to_support(traceback.format_exc())


async def handle_incoming_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.effective_message
        user_id = message.from_user.id
        chat_id = message.chat_id

        # Only respond if enabled
        is_user_enabled = await db.chatgpt_users.find_one({"user_id": user_id})
        is_group_enabled = await db.chatgpt_groups.find_one({"chat_id": chat_id})

        if not (is_user_enabled or is_group_enabled):
            return

        user_text = message.text
        if not user_text:
            return

        reply = await get_chatgpt_response(user_text)
        if reply:
            await message.reply_text(f"```\n{reply}\n```", parse_mode="Markdown")
    except Exception:
        await send_error_to_support(traceback.format_exc())


async def get_chatgpt_response(text: str) -> str:
    try:
        response = await openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text}]
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "⚠️ Error getting reply from ChatGPT."


def setup(app):
    app.add_handler(CommandHandler("chatgpt", chatgpt_command))
    app.add_handler(CallbackQueryHandler(handle_chatgpt_toggle, pattern="^chatgpt:"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_incoming_message))


def get_info():
    return {
        "name": "ChatGPT Plugin 🤖",
        "description": "ChatGPT replies to messages when enabled by user or admin."
    }


async def test():
    assert OPENAI_API_KEY is not None, "OPENAI_API_KEY not set"
    await db.command("ping")    
    app.add_handler(CommandHandler("chatgpt", chatgpt_command))
    app.add_handler(CallbackQueryHandler(handle_chatgpt_toggle, pattern="chatgpt:"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_incoming_message))

async def test():
    assert OPENAI_API_KEY is not None, "OPENAI_API_KEY not set"
    await db.command("ping")        
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
