from telegram import Update, User
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from plugins.db import db, send_log, send_error_to_support
from pymongo.errors import DuplicateKeyError
from telegram.helpers import escape_markdown

async def track_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This part of your code seems correct, so we will keep it.
    user: User = update.effective_user
    if not user:
        return

    # Check if the update is from a new chat member event
    if update.message and update.message.new_chat_members:
        # Loop through all new members
        for new_member in update.message.new_chat_members:
            # We want to track the user who is not the bot itself
            if not new_member.is_bot:
                user_data = {
                    "_id": new_member.id,
                    "name": new_member.first_name or "Unknown"
                }

                try:
                    await db.users.insert_one(user_data)
                    count = await db.users.count_documents({})
                    escaped_name = escape_markdown(new_member.first_name or "Unknown", version=2)
                    escaped_id = escape_markdown(str(new_member.id), version=2)
                    escaped_count = escape_markdown(str(count), version=2)
                    await send_log(
                        f"🎉 *New user joined:*\n"
                        f"`{escaped_name}` (`{escaped_id}`)\n"
                        f"👥 *Total users:* `{escaped_count}`"
                    )

                except DuplicateKeyError:
                    pass
                except Exception as e:
                    await send_error_to_support(e, "user_tracker")
    # You might also want to handle private messages to the bot to track them
    elif update.message and update.message.chat.type == "private":
        user_data = {
            "_id": user.id,
            "name": user.first_name or "Unknown"
        }
        try:
            await db.users.insert_one(user_data)
            count = await db.users.count_documents({})
            escaped_name = escape_markdown(user.first_name or "Unknown", version=2)
            escaped_id = escape_markdown(str(user.id), version=2)
            escaped_count = escape_markdown(str(count), version=2)
            await send_log(
                f"🎉 *New user started a chat:*\n"
                f"`{escaped_name}` (`{escaped_id}`)\n"
                f"👥 *Total users:* `{escaped_count}`"
            )
        except DuplicateKeyError:
            pass
        except Exception as e:
            await send_error_to_support(e, "user_tracker")
    # This will handle any message that isn't a new chat member or a private message.
    # It will ensure that we track any user that interacts with the bot.
    else:
        user_data = {
            "_id": user.id,
            "name": user.first_name or "Unknown"
        }
        try:
            await db.users.insert_one(user_data)
        except DuplicateKeyError:
            pass
        except Exception as e:
            await send_error_to_support(e, "user_tracker")

def setup(app: Application):
    # This handler will track new members joining a group
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_user))
    # This handler will track users that start a conversation with the bot
    app.add_handler(MessageHandler(filters.COMMAND | filters.TEXT, track_user))

def get_info():
    return {
        "name": "User Tracker",
        "description": "Tracks every unique user globally for future broadcasts."
    }

async def test():
    await db.users.estimated_document_count()
