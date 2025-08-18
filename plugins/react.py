import traceback
import os
import random
from telegram import Update, Bot, ReactionTypeEmoji, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters
from plugins.db import db  # MongoDB instance

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")

SUPPORTED_REACTIONS = [
    "👍","👎","❤","🔥","🥰","👏","😁","🤔","🤯","😱",
    "🤬","😢","🎉","🤩","🤮","💩","🙏","👌","🤡","💔","🤣"
]

async def send_error_to_support(error: Exception, where="react_plugin"):
    if not BOT_TOKEN or not SUPPORT_CHAT_ID:
        return
    bot = Bot(BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=(f"❗️ *Plugin Error: {where}*\n"
                  f"`{str(error)}`\n\n"
                  f"```{traceback.format_exc()}```")[:4000],
            parse_mode="MarkdownV2"
        )
    except Exception:
        pass

async def reaction_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = update.effective_chat
        if chat.type == "private":
            await update.message.reply_text("🚫 This command works in groups only.")
            return

        user = update.effective_user
        member = await chat.get_member(user.id)
        if member.status not in ("administrator", "creator"):
            await update.message.reply_text("🚫 Only admins can configure reactions.")
            return

        chat_settings = await db.reactions.find_one({"chat_id": chat.id})
        enabled = chat_settings.get("enabled", False) if chat_settings else False

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Enable", callback_data=f"react_enable:{chat.id}"),
            InlineKeyboardButton("❌ Disable", callback_data=f"react_disable:{chat.id}")
        ]])

        await update.message.reply_text(
            f"🎭 Reactions are currently: {'✅ ON' if enabled else '❌ OFF'}",
            reply_markup=keyboard
        )
    except Exception as e:
        await send_error_to_support(e, "reaction_settings")

async def toggle_react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        chat = update.effective_chat
        user = update.effective_user
        member = await chat.get_member(user.id)
        if member.status not in ("administrator", "creator"):
            await query.edit_message_text("🚫 Only admins can toggle reactions.")
            return

        action, chat_id = query.data.split(":")
        chat_id = int(chat_id)
        new_state = True if action == "react_enable" else False

        await db.reactions.update_one({"chat_id": chat_id}, {"$set": {"enabled": new_state}}, upsert=True)

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Enable", callback_data=f"react_enable:{chat_id}"),
            InlineKeyboardButton("❌ Disable", callback_data=f"react_disable:{chat_id}")
        ]])

        await query.edit_message_text(
            f"🎭 Reactions are now: {'✅ ON' if new_state else '❌ OFF'}",
            reply_markup=keyboard
        )
    except Exception as e:
        await send_error_to_support(e, "toggle_react")

async def react_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return

        chat_id = update.effective_chat.id
        # ignore messages from spam plugin user input
        if context.user_data.get("sspam_user") == update.effective_user.id and \
           context.user_data.get("sspam_chat") == chat_id:
            return

        chat_settings = await db.reactions.find_one({"chat_id": chat_id})
        if not chat_settings or not chat_settings.get("enabled", False):
            return

        emoji = random.choice(SUPPORTED_REACTIONS)
        await update.message.set_reaction([ReactionTypeEmoji(emoji=emoji)])
    except Exception as e:
        await send_error_to_support(e, "react_to_message")

def get_info():
    return {
        "name": "Reaction Plugin 🎭",
        "description": "Auto-reacts to all messages, toggleable by admins with inline buttons."
    }

def setup(app):
    app.add_handler(CommandHandler("reactsettings", reaction_settings))
    app.add_handler(CallbackQueryHandler(toggle_react, pattern=r"^react_"))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, react_to_message))

async def test():
    return "✅ React plugin loaded successfully"
