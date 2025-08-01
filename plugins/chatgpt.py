import os
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from openai import AsyncOpenAI
from plugins.db import db
from plugins.db import send_error_to_support

# --- Environment and API Setup ---
# Fetches the OpenAI API key from your environment variables.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initializes the asynchronous OpenAI client.
openai = AsyncOpenAI(api_key=OPENAI_API_KEY)
# Connects to the 'chatgpt_settings' collection in your MongoDB database.
SETTINGS = db.chatgpt_settings

# --- Helper Functions ---

async def is_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """Checks if a user is an administrator or creator of a chat."""
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except Exception:
        # If the bot fails to get chat member (e.g., permissions), assume not admin.
        return False

# --- Command and Message Handlers ---

async def chatgpt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /chatgpt command.
    Displays toggle buttons for enabling/disabling ChatGPT for the user or the entire group.
    """
    try:
        user = update.effective_user
        chat = update.effective_chat
        
        # Fetch current settings from the database or create a new empty doc.
        doc = await SETTINGS.find_one({"chat_id": chat.id}) or {}
        enabled_users = doc.get("enabled_users", [])
        group_enabled = doc.get("group_enabled", False)

        # Create inline keyboard buttons. The group toggle is only shown to admins.
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
        # Clean up the button list to remove any None values (e.g., if group toggle is hidden).
        buttons = [[b for b in row if b] for row in buttons if any(row)]

        await update.message.reply_text(
            "ChatGPT toggle options:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception:
        await send_error_to_support(traceback.format_exc())


async def chatgpt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles callbacks from the inline keyboard buttons.
    Toggles user-specific or group-wide settings and updates the message markup.
    """
    try:
        query = update.callback_query
        user = query.from_user
        chat = query.message.chat
        data = query.data

        # Fetch current settings to modify them.
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
            # Update the database with the new list of enabled users.
            await SETTINGS.update_one({"chat_id": chat.id}, {"$set": {"enabled_users": enabled_users}}, upsert=True)

        elif data == "chatgpt_toggle_group":
            # Ensure the user is an admin before changing group settings.
            if not await is_admin(context, chat.id, user.id):
                await query.answer("Only admins can toggle the group setting.", show_alert=True)
                return
            group_enabled = not group_enabled
            # Update the database with the new group-wide setting.
            await SETTINGS.update_one({"chat_id": chat.id}, {"$set": {"group_enabled": group_enabled}}, upsert=True)
            await query.answer("✅ Toggled group-wide setting")

        # After any change, refetch the settings to rebuild the keyboard.
        new_doc = await SETTINGS.find_one({"chat_id": chat.id}) or {}
        new_enabled_users = new_doc.get("enabled_users", [])
        new_group_enabled = new_doc.get("group_enabled", False)

        # Recreate the buttons with updated state indicators (✅).
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

        # Edit the original message to show the updated buttons.
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))

    except Exception:
        await send_error_to_support(f"chatgpt_callback error:\n`{traceback.format_exc()}`")


async def chatgpt_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processes incoming text messages.
    If ChatGPT is enabled for the user or group, it sends the message to OpenAI and replies.
    """
    try:
        # Ignore updates without a message.
        if not update.message or not update.effective_chat or not update.effective_user:
            return

        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        text = update.message.text
        
        # Ignore empty messages or commands.
        if not text or text.startswith("/"):
            return

        # Check if the feature is enabled for this chat.
        doc = await SETTINGS.find_one({"chat_id": chat_id}) or {}
        enabled_users = doc.get("enabled_users", [])
        group_enabled = doc.get("group_enabled", False)

        # If the user has not enabled it individually and it's not enabled for the group, do nothing.
        if user_id not in enabled_users and not group_enabled:
            return

        # Call the OpenAI API to get a completion.
        res = await openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text}]
        )
        reply = res.choices[0].message.content.strip()

        # Reply to the user's message with the response from ChatGPT.
        await update.message.reply_text(f"```\n{reply}\n```", parse_mode="Markdown")
        
    except Exception:
        await send_error_to_support(f"chatgpt_reply error:\n`{traceback.format_exc()}`")


# --- Plugin Setup and Metadata ---

def setup(app):
    """Registers the handlers with the application."""
    app.add_handler(CommandHandler("chatgpt", chatgpt_command))
    app.add_handler(CallbackQueryHandler(chatgpt_callback, pattern="^chatgpt_toggle_"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chatgpt_reply))


def get_info():
    """Returns basic information about the plugin."""
    return {
        "name": "ChatGPT Plugin 🤖",
        "description": "ChatGPT replies to messages when enabled by user or admin."
    }


async def test():
    """Performs a self-check to ensure the plugin is configured correctly."""
    assert OPENAI_API_KEY, "ChatGPT API key not set"
    assert db is not None, "MongoDB not connected"
    await db.command("ping")

