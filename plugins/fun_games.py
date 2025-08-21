"""
Fun Games Plugin for LunaBot
Provides entertaining games and interactive features
"""

import os
import random
import traceback
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from .db import db, send_log, send_error_to_support

# Collections
games_collection = db["games"]
trivia_collection = db["trivia"]

# Game data
TRIVIA_QUESTIONS = [
    {
        "question": "What is the capital of France?",
        "options": ["London", "Berlin", "Paris", "Madrid"],
        "correct": 2,
        "category": "Geography"
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "options": ["Venus", "Mars", "Jupiter", "Saturn"],
        "correct": 1,
        "category": "Science"
    },
    {
        "question": "Who painted the Mona Lisa?",
        "options": ["Van Gogh", "Picasso", "Da Vinci", "Monet"],
        "correct": 2,
        "category": "Art"
    },
    {
        "question": "What is the largest mammal in the world?",
        "options": ["Elephant", "Blue Whale", "Giraffe", "Hippopotamus"],
        "correct": 1,
        "category": "Nature"
    },
    {
        "question": "In which year did World War II end?",
        "options": ["1944", "1945", "1946", "1947"],
        "correct": 1,
        "category": "History"
    },
    {
        "question": "What is the chemical symbol for gold?",
        "options": ["Go", "Gd", "Au", "Ag"],
        "correct": 2,
        "category": "Science"
    },
    {
        "question": "Which country invented pizza?",
        "options": ["France", "Italy", "Greece", "Spain"],
        "correct": 1,
        "category": "Food"
    },
    {
        "question": "What is the fastest land animal?",
        "options": ["Lion", "Cheetah", "Leopard", "Tiger"],
        "correct": 1,
        "category": "Nature"
    },
    {
        "question": "How many continents are there?",
        "options": ["5", "6", "7", "8"],
        "correct": 2,
        "category": "Geography"
    },
    {
        "question": "What is the smallest country in the world?",
        "options": ["Monaco", "Vatican City", "San Marino", "Liechtenstein"],
        "correct": 1,
        "category": "Geography"
    }
]

RIDDLES = [
    {
        "riddle": "I have keys but no locks. I have space but no room. You can enter, but you can't go outside. What am I?",
        "answer": "keyboard",
        "hint": "You use it to type!"
    },
    {
        "riddle": "The more you take, the more you leave behind. What am I?",
        "answer": "footsteps",
        "hint": "Think about walking!"
    },
    {
        "riddle": "I'm tall when I'm young, and short when I'm old. What am I?",
        "answer": "candle",
        "hint": "It burns and melts!"
    },
    {
        "riddle": "What has hands but cannot clap?",
        "answer": "clock",
        "hint": "It tells time!"
    },
    {
        "riddle": "What gets wet while drying?",
        "answer": "towel",
        "hint": "You use it after a shower!"
    }
]

WORD_GAMES = [
    {
        "word": "PYTHON",
        "hint": "A programming language named after a snake",
        "category": "Technology"
    },
    {
        "word": "RAINBOW",
        "hint": "Colorful arc in the sky after rain",
        "category": "Nature"
    },
    {
        "word": "TELESCOPE",
        "hint": "Device used to see distant objects",
        "category": "Science"
    },
    {
        "word": "BUTTERFLY",
        "hint": "Colorful insect that was once a caterpillar",
        "category": "Nature"
    },
    {
        "word": "CHOCOLATE",
        "hint": "Sweet treat made from cocoa",
        "category": "Food"
    }
]

async def start_trivia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Start a trivia game
    """
    try:
        question_data = random.choice(TRIVIA_QUESTIONS)
        
        # Create keyboard with options
        keyboard = []
        for i, option in enumerate(question_data["options"]):
            keyboard.append([InlineKeyboardButton(f"{chr(65+i)}. {option}", callback_data=f"trivia_{i}")])
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="trivia_cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        trivia_text = f"🧠 **Trivia Time!**\n"
        trivia_text += f"**Category:** {question_data['category']}\n\n"
        trivia_text += f"**Question:** {question_data['question']}"
        
        message = await update.message.reply_text(trivia_text, reply_markup=reply_markup)
        
        # Store game data
        game_data = {
            "chat_id": update.effective_chat.id,
            "message_id": message.message_id,
            "user_id": update.effective_user.id,
            "game_type": "trivia",
            "question_data": question_data,
            "start_time": datetime.utcnow(),
            "status": "active"
        }
        
        await games_collection.insert_one(game_data)
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Start Trivia Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def start_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Start a riddle game
    """
    try:
        riddle_data = random.choice(RIDDLES)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💡 Get Hint", callback_data="riddle_hint")],
            [InlineKeyboardButton("🤔 Give Up", callback_data="riddle_giveup")]
        ])
        
        riddle_text = f"🤔 **Riddle Time!**\n\n"
        riddle_text += f"**Riddle:** {riddle_data['riddle']}\n\n"
        riddle_text += "Type your answer in the chat!"
        
        message = await update.message.reply_text(riddle_text, reply_markup=keyboard)
        
        # Store game data
        game_data = {
            "chat_id": update.effective_chat.id,
            "message_id": message.message_id,
            "user_id": update.effective_user.id,
            "game_type": "riddle",
            "riddle_data": riddle_data,
            "start_time": datetime.utcnow(),
            "status": "active",
            "hint_used": False
        }
        
        await games_collection.insert_one(game_data)
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Start Riddle Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def start_word_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Start a word guessing game
    """
    try:
        word_data = random.choice(WORD_GAMES)
        word = word_data["word"]
        
        # Create scrambled word
        scrambled = ''.join(random.sample(word, len(word)))
        while scrambled == word:  # Make sure it's actually scrambled
            scrambled = ''.join(random.sample(word, len(word)))
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💡 Get Hint", callback_data="word_hint")],
            [InlineKeyboardButton("🤔 Give Up", callback_data="word_giveup")]
        ])
        
        word_text = f"🔤 **Word Game!**\n\n"
        word_text += f"**Scrambled Word:** `{scrambled}`\n"
        word_text += f"**Category:** {word_data['category']}\n\n"
        word_text += "Unscramble the letters to find the word!"
        
        message = await update.message.reply_text(word_text, reply_markup=keyboard)
        
        # Store game data
        game_data = {
            "chat_id": update.effective_chat.id,
            "message_id": message.message_id,
            "user_id": update.effective_user.id,
            "game_type": "word",
            "word_data": word_data,
            "scrambled": scrambled,
            "start_time": datetime.utcnow(),
            "status": "active",
            "hint_used": False
        }
        
        await games_collection.insert_one(game_data)
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Start Word Game Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def dice_roll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Roll dice
    """
    try:
        # Default to 1 die with 6 sides
        num_dice = 1
        num_sides = 6
        
        if context.args:
            try:
                if len(context.args) == 1:
                    num_dice = int(context.args[0])
                elif len(context.args) == 2:
                    num_dice = int(context.args[0])
                    num_sides = int(context.args[1])
            except ValueError:
                await update.message.reply_text("❌ Invalid format. Use: `/dice [number_of_dice] [sides]`")
                return
        
        # Limit dice and sides
        num_dice = min(max(num_dice, 1), 10)
        num_sides = min(max(num_sides, 2), 100)
        
        results = [random.randint(1, num_sides) for _ in range(num_dice)]
        total = sum(results)
        
        dice_text = f"🎲 **Dice Roll Results**\n\n"
        dice_text += f"**Dice:** {num_dice}d{num_sides}\n"
        dice_text += f"**Results:** {', '.join(map(str, results))}\n"
        dice_text += f"**Total:** {total}"
        
        await update.message.reply_text(dice_text)
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Dice Roll Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def coin_flip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Flip a coin
    """
    try:
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙" if result == "Heads" else "🔄"
        
        await update.message.reply_text(f"{emoji} **Coin Flip Result:** {result}")
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Coin Flip Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def rock_paper_scissors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Play Rock Paper Scissors
    """
    try:
        if not context.args:
            await update.message.reply_text(
                "✂️ **Rock Paper Scissors**\n\n"
                "Usage: `/rps rock`, `/rps paper`, or `/rps scissors`"
            )
            return
        
        user_choice = context.args[0].lower()
        if user_choice not in ['rock', 'paper', 'scissors']:
            await update.message.reply_text("❌ Invalid choice. Use: rock, paper, or scissors")
            return
        
        bot_choice = random.choice(['rock', 'paper', 'scissors'])
        
        # Determine winner
        if user_choice == bot_choice:
            result = "It's a tie!"
            emoji = "🤝"
        elif (user_choice == 'rock' and bot_choice == 'scissors') or \
             (user_choice == 'paper' and bot_choice == 'rock') or \
             (user_choice == 'scissors' and bot_choice == 'paper'):
            result = "You win!"
            emoji = "🎉"
        else:
            result = "I win!"
            emoji = "🤖"
        
        choice_emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
        
        rps_text = f"✂️ **Rock Paper Scissors**\n\n"
        rps_text += f"**You:** {choice_emojis[user_choice]} {user_choice.title()}\n"
        rps_text += f"**Me:** {choice_emojis[bot_choice]} {bot_choice.title()}\n\n"
        rps_text += f"{emoji} **{result}**"
        
        await update.message.reply_text(rps_text)
        
    except Exception as e:
        await send_error_to_support(
            f"*❌ Rock Paper Scissors Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def handle_game_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle messages that might be answers to active games
    """
    try:
        if not update.message.text:
            return
            
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        message_text = update.message.text.lower().strip()
        
        # Check for active games
        active_game = await games_collection.find_one({
            "chat_id": chat_id,
            "user_id": user_id,
            "status": "active"
        })
        
        if not active_game:
            return
            
        if active_game["game_type"] == "riddle":
            correct_answer = active_game["riddle_data"]["answer"].lower()
            if message_text == correct_answer:
                # Correct answer!
                await games_collection.update_one(
                    {"_id": active_game["_id"]},
                    {"$set": {"status": "completed", "end_time": datetime.utcnow()}}
                )
                
                time_taken = datetime.utcnow() - active_game["start_time"]
                
                success_text = f"🎉 **Correct!**\n\n"
                success_text += f"**Answer:** {active_game['riddle_data']['answer']}\n"
                success_text += f"**Time:** {time_taken.seconds} seconds"
                if active_game.get("hint_used"):
                    success_text += "\n💡 (Hint was used)"
                
                await update.message.reply_text(success_text)
                
        elif active_game["game_type"] == "word":
            correct_word = active_game["word_data"]["word"].lower()
            if message_text == correct_word:
                # Correct answer!
                await games_collection.update_one(
                    {"_id": active_game["_id"]},
                    {"$set": {"status": "completed", "end_time": datetime.utcnow()}}
                )
                
                time_taken = datetime.utcnow() - active_game["start_time"]
                
                success_text = f"🎉 **Correct!**\n\n"
                success_text += f"**Word:** {active_game['word_data']['word']}\n"
                success_text += f"**Time:** {time_taken.seconds} seconds"
                if active_game.get("hint_used"):
                    success_text += "\n💡 (Hint was used)"
                
                await update.message.reply_text(success_text)
                
    except Exception as e:
        await send_error_to_support(
            f"*❌ Handle Game Message Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle game button callbacks
    """
    try:
        query = update.callback_query
        await query.answer()
        
        chat_id = query.message.chat.id
        message_id = query.message.message_id
        user_id = query.from_user.id
        
        # Find the game
        game = await games_collection.find_one({
            "chat_id": chat_id,
            "message_id": message_id,
            "status": "active"
        })
        
        if not game:
            await query.edit_message_text("❌ Game not found or already completed.")
            return
            
        if game["user_id"] != user_id:
            await query.answer("❌ This is not your game!", show_alert=True)
            return
            
        if query.data.startswith("trivia_"):
            if query.data == "trivia_cancel":
                await games_collection.update_one(
                    {"_id": game["_id"]},
                    {"$set": {"status": "cancelled"}}
                )
                await query.edit_message_text("❌ Trivia cancelled.")
                return
                
            selected_option = int(query.data.split("_")[1])
            correct_option = game["question_data"]["correct"]
            
            await games_collection.update_one(
                {"_id": game["_id"]},
                {"$set": {"status": "completed", "end_time": datetime.utcnow()}}
            )
            
            if selected_option == correct_option:
                result_text = f"✅ **Correct!**\n\n"
                result_text += f"**Answer:** {game['question_data']['options'][correct_option]}"
            else:
                result_text = f"❌ **Wrong!**\n\n"
                result_text += f"**Your answer:** {game['question_data']['options'][selected_option]}\n"
                result_text += f"**Correct answer:** {game['question_data']['options'][correct_option]}"
                
            await query.edit_message_text(result_text)
            
        elif query.data.startswith("riddle_"):
            if query.data == "riddle_hint":
                await games_collection.update_one(
                    {"_id": game["_id"]},
                    {"$set": {"hint_used": True}}
                )
                
                hint_text = f"💡 **Hint:** {game['riddle_data']['hint']}"
                await query.answer(hint_text, show_alert=True)
                
            elif query.data == "riddle_giveup":
                await games_collection.update_one(
                    {"_id": game["_id"]},
                    {"$set": {"status": "given_up"}}
                )
                
                giveup_text = f"🤔 **Answer:** {game['riddle_data']['answer']}\n\n"
                giveup_text += "Better luck next time!"
                await query.edit_message_text(giveup_text)
                
        elif query.data.startswith("word_"):
            if query.data == "word_hint":
                await games_collection.update_one(
                    {"_id": game["_id"]},
                    {"$set": {"hint_used": True}}
                )
                
                hint_text = f"💡 **Hint:** {game['word_data']['hint']}"
                await query.answer(hint_text, show_alert=True)
                
            elif query.data == "word_giveup":
                await games_collection.update_one(
                    {"_id": game["_id"]},
                    {"$set": {"status": "given_up"}}
                )
                
                giveup_text = f"🔤 **Answer:** {game['word_data']['word']}\n\n"
                giveup_text += "Better luck next time!"
                await query.edit_message_text(giveup_text)
                
    except Exception as e:
        await send_error_to_support(
            f"*❌ Game Callback Error:*\n`{str(e)}`\n```{traceback.format_exc()}```"
        )

def setup(app: Application) -> None:
    """
    Setup function called by the main bot to register handlers
    """
    # Command handlers
    app.add_handler(CommandHandler("trivia", start_trivia))
    app.add_handler(CommandHandler("riddle", start_riddle))
    app.add_handler(CommandHandler("wordgame", start_word_game))
    app.add_handler(CommandHandler("dice", dice_roll))
    app.add_handler(CommandHandler("coinflip", coin_flip))
    app.add_handler(CommandHandler("flip", coin_flip))
    app.add_handler(CommandHandler("rps", rock_paper_scissors))
    
    # Message handler for game answers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game_message))
    
    # Callback query handler for game buttons
    app.add_handler(CallbackQueryHandler(game_callback, pattern="^(trivia_|riddle_|word_)"))

async def test() -> None:
    """
    Test function to verify the plugin works correctly
    """
    # Test database connection
    await db.command("ping")

def get_info() -> dict:
    """
    Return plugin information
    """
    return {
        "name": "Fun Games",
        "description": "Interactive games and entertainment features",
        "version": "1.0.0",
        "commands": [
            "/trivia - Start a trivia question",
            "/riddle - Get a riddle to solve",
            "/wordgame - Play word unscrambling game",
            "/dice [num] [sides] - Roll dice",
            "/coinflip or /flip - Flip a coin",
            "/rps <choice> - Play Rock Paper Scissors"
        ],
        "features": [
            "Multiple choice trivia questions",
            "Riddles with hints",
            "Word unscrambling games",
            "Dice rolling with custom sides",
            "Coin flipping",
            "Rock Paper Scissors"
        ]
    }

