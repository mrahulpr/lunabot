from telegram import Update, User
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from plugins.db import db, send_log, send_error_to_support
from pymongo.errors import DuplicateKeyError
from telegram.helpers import escape_markdown

async def track_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Tracks new users who join a chat or start a private conversation with the bot.
    It also logs the total user count.
    """
    user: User = update.effective_user
    if not user:
        return

    # Handle new chat members joining a group
    if update.message and update.message.new_chat_members:
        # Loop through all new members that are not the bot itself
        for new_member in update.message.new_chat_members:
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
                    pass  # User already exists, no need to log
                except Exception as e:
                    await send_error_to_support(e, "user_tracker_new_member")

    # Handle users starting a private chat with the bot or sending any message
    else:
        user_data = {
            "_id": user.id,
            "name": user.first_name or "Unknown"
        }

        try:
            # Try to insert the user, will fail if they already exist
            await db.users.insert_one(user_data)
            count = await db.users.count_documents({})
            
            escaped_name = escape_markdown(user.first_name or "Unknown", version=2)
            escaped_id = escape_markdown(str(user.id), version=2)
            escaped_count = escape_markdown(str(count), version=2)

            # Log this new user since they weren't in the database
            await send_log(
                f"🎉 *New user started a chat:*\n"
                f"`{escaped_name}` (`{escaped_id}`)\n"
                f"👥 *Total users:* `{escaped_count}`"
            )

        except DuplicateKeyError:
            pass  # User already tracked, ignore
        except Exception as e:
            await send_error_to_support(e, "user_tracker_general")

def setup(app: Application):
    """
    Sets up the message handlers to track users.
    """
    # This handler triggers when a new user joins a group
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_user))
    
    # This handler triggers for any other messages (commands, text, etc.)
    # It will track users who start a private chat or send their first message.
    app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.NEW_CHAT_MEMBERS, track_user))


def get_info():
    return {
        "name": "User Tracker",
        "description": "Tracks every unique user globally for future broadcasts."
    }

async def test():
    await db.users.estimated_document_count()
