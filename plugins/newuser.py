from telegram import Update, User
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from plugins.db import db, send_log, send_error_to_support
from pymongo.errors import DuplicateKeyError

async def track_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user: User = update.effective_user
    if not user:
        return

    user_data = {
        "_id": user.id,
        "name": user.first_name or "Unknown"
    }

    try:
        await db.users.insert_one(user_data)
        count = await db.users.count_documents({})
        await send_log(
            f"🎉 *New user joined:*\n"
            f"`{user.first_name}` (`{user.id}`)\n"
            f"👥 *Total users:* `{count}`"
        )
    except DuplicateKeyError:
        pass  # User already tracked, ignore
    except Exception as e:
        await send_error_to_support(e, "user_tracker")

def setup(app: Application):
    app.add_handler(MessageHandler(filters.ALL, track_user))

def get_info():
    return {
        "name": "User Tracker",
        "description": "Tracks every unique user globally for future broadcasts."
    }

async def test():
    await db.users.estimated_document_count()
