"""
Group Management Plugin for LunaBot
Provides fun and interactive features for group management
"""

import os
import random
import traceback
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from .db import db, send_log, send_error_to_support

# Collections
groups_collection = db["groups"]
warnings_collection = db["warnings"]
polls_collection = db["polls"]

# Fun responses and data
WELCOME_MESSAGES = [
    "🎉 Welcome {name}! Great to have you here!",
    "👋 Hey {name}! Welcome to our awesome group!",
    "🌟 {name} just joined! Let's give them a warm welcome!",
    "🎊 Welcome aboard {name}! Hope you enjoy your stay!",
    "🚀 {name} has landed! Welcome to the group!"
]

GOODBYE_MESSAGES = [
    "👋 Goodbye {name}! Thanks for being part of our community!",
    "🌅 {name} has left the building! We'll miss you!",
    "✨ Farewell {name}! Hope to see you again soon!",
    "🎭 {name} has exited stage left! Take care!",
    "🌊 {name} sailed away! Safe travels!"
]

TRUTH_QUESTIONS = [
    "What's the most embarrassing thing you've done in public?",
    "What's your biggest fear?",
    "What's the weirdest food combination you actually enjoy?",
    "What's your most useless talent?",
    "What's the last lie you told?",
    "What's your guilty pleasure?",
    "What's the strangest dream you've ever had?",
    "What's your most irrational fear?",
    "What's the worst advice you've ever given?",
    "What's your secret talent that no one knows about?"
]

DARE_CHALLENGES = [
    "Send a voice message singing your favorite song",
    "Change your profile picture to something funny for 24 hours",
    "Send a selfie making the silliest face you can",
    "Write a short poem about the last thing you ate",
    "Do 10 jumping jacks and send a video",
    "Text someone 'I love you' (screenshot proof required)",
    "Post an embarrassing childhood photo",
    "Speak in rhymes for the next 10 messages",
    "Do your best impression of a famous person",
    "Send a voice message in a funny accent"
]

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Welcome new group members
    """
    try:
        if not update.message.new_chat_members:
            return
            
        chat = update.effective_chat
        if chat.type not in ['group', 'supergroup']:
            return
            
        for new_member in update.message.new_chat_members:
            if new_member.is_bot:
                continue
                
            name = new_member.first_name or new_member.username or "New Member"
            welcome_msg = random.choice(WELCOME_MESSAGES).format(name=name)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👋 Say Hi!", callback_data=f"welcome_hi_{new_member.id}")]
            ])
            
            await update.message.reply_text(welcome_msg, reply_markup=keyboard)
            
            # Store group info
            await groups_collection.update_one(
                {"chat_id": chat.id},
                {
                    "$set": {
                        "chat_title": chat.title,
                        "chat_type": chat.type,
                        "last_activity": datetime.utcnow()
                    },
                    "$inc": {"member_count": 1}
                },
                upsert=True
            )
            
    except Exception as e:
        await send_error_to_support(
            f"*❌ Welcome Member Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def goodbye_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Say goodbye to leaving members
    """
    try:
        if not update.message.left_chat_member:
            return
            
        chat = update.effective_chat
        if chat.type not in ['group', 'supergroup']:
            return
            
        left_member = update.message.left_chat_member
        if left_member.is_bot:
            return
            
        name = left_member.first_name or left_member.username or "Member"
        goodbye_msg = random.choice(GOODBYE_MESSAGES).format(name=name)
        
        await update.message.reply_text(goodbye_msg)
        
        # Update group info
        await groups_collection.update_one(
            {"chat_id": chat.id},
            {
                "$set": {"last_activity": datetime.utcnow()},
                "$inc": {"member_count": -1}
            }
        )
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Goodbye Member Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Warn a user in the group
    """
    try:
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ This command can only be used in groups.")
            return
            
        # Check if user is admin
        member = await chat.get_member(user.id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Only admins can warn users.")
            return
            
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Reply to a message to warn the user.")
            return
            
        warned_user = update.message.reply_to_message.from_user
        reason = " ".join(context.args) if context.args else "No reason provided"
        
        # Add warning to database
        warning_data = {
            "chat_id": chat.id,
            "user_id": warned_user.id,
            "warned_by": user.id,
            "reason": reason,
            "timestamp": datetime.utcnow()
        }
        
        await warnings_collection.insert_one(warning_data)
        
        # Count total warnings for this user in this chat
        warning_count = await warnings_collection.count_documents({
            "chat_id": chat.id,
            "user_id": warned_user.id
        })
        
        warning_text = f"⚠️ **Warning #{warning_count}**\n"
        warning_text += f"**User:** {warned_user.first_name or warned_user.username}\n"
        warning_text += f"**Reason:** {reason}\n"
        warning_text += f"**Warned by:** {user.first_name or user.username}"
        
        if warning_count >= 3:
            warning_text += "\n\n🚨 **User has reached 3 warnings!**"
            
        await update.message.reply_text(warning_text)
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Warn User Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def truth_or_dare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Truth or Dare game
    """
    try:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🤔 Truth", callback_data="tod_truth"),
                InlineKeyboardButton("😈 Dare", callback_data="tod_dare")
            ],
            [InlineKeyboardButton("🎲 Random", callback_data="tod_random")]
        ])
        
        await update.message.reply_text(
            "🎮 **Truth or Dare?**\n\nChoose your challenge!",
            reply_markup=keyboard
        )
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Truth or Dare Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def group_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show group statistics
    """
    try:
        chat = update.effective_chat
        
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ This command can only be used in groups.")
            return
            
        # Get group data
        group_data = await groups_collection.find_one({"chat_id": chat.id})
        
        # Get member count
        member_count = await chat.get_member_count()
        
        # Get warning count
        warning_count = await warnings_collection.count_documents({"chat_id": chat.id})
        
        stats_text = f"📊 **Group Statistics**\n\n"
        stats_text += f"**Group:** {chat.title}\n"
        stats_text += f"**Members:** {member_count}\n"
        stats_text += f"**Total Warnings:** {warning_count}\n"
        
        if group_data:
            if group_data.get('last_activity'):
                stats_text += f"**Last Activity:** {group_data['last_activity'].strftime('%Y-%m-%d %H:%M')}\n"
                
        await update.message.reply_text(stats_text)
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Group Stats Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Share a random fun fact
    """
    try:
        facts = [
            "🐙 Octopuses have three hearts and blue blood!",
            "🍯 Honey never spoils. Archaeologists have found edible honey in ancient Egyptian tombs!",
            "🦒 A giraffe's tongue is about 20 inches long and is dark blue to prevent sunburn!",
            "🌙 The Moon is moving away from Earth at about 1.5 inches per year!",
            "🐧 Penguins can jump up to 6 feet out of water!",
            "🧠 Your brain uses about 20% of your body's total energy!",
            "🦋 Butterflies taste with their feet!",
            "🌊 The Pacific Ocean is larger than all land masses combined!",
            "⚡ Lightning strikes the Earth about 100 times per second!",
            "🐨 Koalas sleep up to 22 hours a day!"
        ]
        
        fact = random.choice(facts)
        await update.message.reply_text(f"🎯 **Random Fact:**\n\n{fact}")
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Random Fact Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def magic_8ball(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Magic 8-ball responses
    """
    try:
        if not context.args:
            await update.message.reply_text("🎱 Ask me a question! Example: `/8ball Will it rain today?`")
            return
            
        responses = [
            "🟢 Yes, definitely!",
            "🟢 It is certain!",
            "🟢 Without a doubt!",
            "🟢 Yes, absolutely!",
            "🟢 You can count on it!",
            "🟡 Most likely!",
            "🟡 Outlook good!",
            "🟡 Signs point to yes!",
            "🟡 Reply hazy, try again!",
            "🟡 Ask again later!",
            "🟡 Better not tell you now!",
            "🟡 Cannot predict now!",
            "🟡 Concentrate and ask again!",
            "🔴 Don't count on it!",
            "🔴 My reply is no!",
            "🔴 My sources say no!",
            "🔴 Outlook not so good!",
            "🔴 Very doubtful!"
        ]
        
        question = " ".join(context.args)
        response = random.choice(responses)
        
        await update.message.reply_text(f"🎱 **Magic 8-Ball**\n\n**Question:** {question}\n**Answer:** {response}")
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Magic 8-Ball Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle button callbacks
    """
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("welcome_hi_"):
            user_id = int(query.data.split("_")[-1])
            if query.from_user.id == user_id:
                await query.edit_message_text("👋 Thanks for saying hi! Welcome to the group! 🎉")
            else:
                await query.edit_message_text("👋 Someone said hi to our new member! 🎉")
                
        elif query.data == "tod_truth":
            truth = random.choice(TRUTH_QUESTIONS)
            await query.edit_message_text(f"🤔 **Truth Question:**\n\n{truth}")
            
        elif query.data == "tod_dare":
            dare = random.choice(DARE_CHALLENGES)
            await query.edit_message_text(f"😈 **Dare Challenge:**\n\n{dare}")
            
        elif query.data == "tod_random":
            if random.choice([True, False]):
                truth = random.choice(TRUTH_QUESTIONS)
                await query.edit_message_text(f"🤔 **Truth Question:**\n\n{truth}")
            else:
                dare = random.choice(DARE_CHALLENGES)
                await query.edit_message_text(f"😈 **Dare Challenge:**\n\n{dare}")
                
    except Exception as e:
        await send_error_to_support(
            f"*❌ Button Callback Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

def setup(app: Application) -> None:
    """
    Setup function called by the main bot to register handlers
    """
    # Message handlers for new/left members
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye_member))
    
    # Command handlers
    app.add_handler(CommandHandler("warn", warn_user))
    app.add_handler(CommandHandler("truthordare", truth_or_dare))
    app.add_handler(CommandHandler("tod", truth_or_dare))
    app.add_handler(CommandHandler("groupstats", group_stats))
    app.add_handler(CommandHandler("randomfact", random_fact))
    app.add_handler(CommandHandler("fact", random_fact))
    app.add_handler(CommandHandler("8ball", magic_8ball))
    
    # Callback query handler for buttons
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^(welcome_hi_|tod_)"))

async def test() -> None:
    """
    Test function to verify the plugin works correctly
    """
    # Test database connection
    await db.command("ping")
    
    # Test that collections exist
    collections = await db.list_collection_names()
    for collection_name in ["groups", "warnings", "polls"]:
        if collection_name not in collections:
            # Collections will be created automatically when first document is inserted
            pass

def get_info() -> dict:
    """
    Return plugin information
    """
    return {
        "name": "Group Management",
        "description": "Fun and interactive features for group management",
        "version": "1.0.0",
        "commands": [
            "/warn - Warn a user (admin only)",
            "/truthordare or /tod - Start a Truth or Dare game",
            "/groupstats - Show group statistics",
            "/randomfact or /fact - Get a random fun fact",
            "/8ball <question> - Ask the magic 8-ball"
        ],
        "features": [
            "Auto welcome/goodbye messages",
            "Warning system for admins",
            "Truth or Dare game",
            "Group statistics tracking",
            "Random facts and magic 8-ball"
        ]
    }

