from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

purge_marks = {}

async def purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to start purging.")
        return

    start_id = update.message.reply_to_message.message_id
    end_id = update.message.message_id
    chat_id = update.effective_chat.id

    count = 0
    for msg_id in range(start_id, end_id):
        try:
            await context.bot.delete_message(chat_id, msg_id)
            count += 1
        except:
            pass

    await update.message.reply_text(f"Purged {count} messages.")

async def spurge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    start_id = update.message.reply_to_message.message_id
    end_id = update.message.message_id
    chat_id = update.effective_chat.id

    for msg_id in range(start_id, end_id):
        try:
            await context.bot.delete_message(chat_id, msg_id)
        except:
            pass

    try:
        await context.bot.delete_message(chat_id, end_id)
    except:
        pass

async def purge_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not context.args:
        await update.message.reply_text("Reply to a message and provide number of messages: /purge <X>")
        return

    try:
        count = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a valid number.")
        return

    chat_id = update.effective_chat.id
    start_id = update.message.reply_to_message.message_id

    for i in range(start_id, start_id + count + 1):
        try:
            await context.bot.delete_message(chat_id, i)
        except:
            pass

async def del_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        try:
            await context.bot.delete_message(update.effective_chat.id, update.message.reply_to_message.message_id)
        except:
            pass
        try:
            await context.bot.delete_message(update.effective_chat.id, update.message.message_id)
        except:
            pass

async def purgefrom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to mark purge start.")
        return

    purge_marks[update.effective_chat.id] = update.message.reply_to_message.message_id
    await update.message.reply_text("Marked the starting point for purge.")

async def purgeto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to mark purge end.")
        return

    if chat_id not in purge_marks:
        await update.message.reply_text("No starting point found. Use /purgefrom first.")
        return

    start_id = purge_marks.pop(chat_id)
    end_id = update.message.reply_to_message.message_id

    if end_id < start_id:
        start_id, end_id = end_id, start_id

    count = 0
    for msg_id in range(start_id, end_id + 1):
        try:
            await context.bot.delete_message(chat_id, msg_id)
            count += 1
        except:
            pass

    await update.message.reply_text(f"Purged {count} messages.")

def get_info():
    return {
        "name": "🧹 Purges",
        "description": "Mass delete messages easily.",
        "commands": ["/purge", "/purge <X>", "/spurge", "/del", "/purgefrom", "/purgeto"]
    }

def setup(app):
    app.add_handler(CommandHandler("purge", purge))
    app.add_handler(CommandHandler("spurge", spurge))
    app.add_handler(CommandHandler("purgefrom", purgefrom))
    app.add_handler(CommandHandler("purgeto", purgeto))
    app.add_handler(CommandHandler("del", del_one))
    app.add_handler(CommandHandler("purge", purge_count, filters.TEXT & filters.Regex(r'^/purge \d+$')))
