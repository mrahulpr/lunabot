"""
User Management Plugin for LunaBot
Handles new user registration and tracking
"""

import os
import traceback
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from .db import db, send_log, send_error_to_support

# Collection for storing user data
users_collection = db["users"]

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Enhanced start command that stores user data and tracks new users
    """
    try:
        user = update.effective_user
        chat = update.effective_chat
        
        # Prepare user data
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code,
            "is_bot": user.is_bot,
            "chat_id": chat.id,
            "chat_type": chat.type,
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "interaction_count": 1
        }
        
        # Check if user already exists
        existing_user = await users_collection.find_one({"user_id": user.id})
        
        if existing_user:
            # Update existing user's last seen and increment interaction count
            await users_collection.update_one(
                {"user_id": user.id},
                {
                    "$set": {
                        "last_seen": datetime.utcnow(),
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name
                    },
                    "$inc": {"interaction_count": 1}
                }
            )
        else:
            # New user - insert into database
            await users_collection.insert_one(user_data)
            
            # Get total user count
            total_users = await users_collection.count_documents({})
            
            # Send notification to support chat about new user
            user_info = f"👤 *New User #{total_users}*\n"
            user_info += f"• *Name:* {user.first_name or 'N/A'}"
            if user.last_name:
                user_info += f" {user.last_name}"
            user_info += f"\n• *Username:* @{user.username or 'N/A'}"
            user_info += f"\n• *User ID:* `{user.id}`"
            user_info += f"\n• *Language:* {user.language_code or 'N/A'}"
            user_info += f"\n• *Chat Type:* {chat.type}"
            user_info += f"\n• *Total Users:* {total_users}"
            
            await send_log(user_info)
            
    except Exception as e:
        await send_error_to_support(
            f"*❌ User Management Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def get_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Command to get user statistics (admin only)
    """
    try:
        user = update.effective_user
        
        # Simple admin check - you can modify this based on your needs
        OWNER_ID = [int(x) for x in os.getenv("OWNER_ID", "").split(",") if x.strip()]
        
        if user.id not in OWNER_ID:
            await update.message.reply_text("❌ You don't have permission to use this command.")
            return
            
        # Get statistics
        total_users = await users_collection.count_documents({})
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new_today = await users_collection.count_documents({"first_seen": {"$gte": today}})
        
        # Get top users by interaction count
        top_users = await users_collection.find({}).sort("interaction_count", -1).limit(5).to_list(length=5)
        
        stats_text = f"📊 *User Statistics*\n\n"
        stats_text += f"• *Total Users:* {total_users}\n"
        stats_text += f"• *New Today:* {new_today}\n\n"
        stats_text += f"*Top Active Users:*\n"
        
        for i, user_doc in enumerate(top_users, 1):
            name = user_doc.get('first_name', 'Unknown')
            username = user_doc.get('username')
            interactions = user_doc.get('interaction_count', 0)
            stats_text += f"{i}\\. {name}"
            if username:
                stats_text += f" \\(@{username}\\)"
            stats_text += f" \\- {interactions} interactions\n"
        
        await update.message.reply_text(stats_text, parse_mode="MarkdownV2")
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ User Stats Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )
        await update.message.reply_text("❌ Error retrieving user statistics.")

def setup(app: Application) -> None:
    """
    Setup function called by the main bot to register handlers
    """
    # Override the default start handler with our enhanced version
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("userstats", get_user_stats))

async def test() -> None:
    """
    Test function to verify the plugin works correctly
    """
    # Test database connection
    await db.command("ping")
    
    # Test that collections exist
    collections = await db.list_collection_names()
    if "users" not in collections:
        # Create the collection if it doesn't exist
        await users_collection.create_index("user_id", unique=True)

def get_info() -> dict:
    """
    Return plugin information
    """
    return {
        "name": "User Management",
        "description": "Tracks new users and provides user statistics",
        "version": "1.0.0",
        "commands": [
            "/start - Enhanced start command with user tracking",
            "/userstats - Get user statistics (admin only)"
        ]
    }

