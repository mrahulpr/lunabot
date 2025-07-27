import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# /wishper command
async def wspr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Inline", callback_data="wishper_inline"),
            InlineKeyboardButton("🔓 Reveal", callback_data="wishper_reveal")
        ],
        [
            InlineKeyboardButton("❌ Delete", callback_data="wishper_delete")
        ]
    ])

    msg = await update.message.reply_text(
        "**🔐 Whisper Created!**\nOnly you can reveal or delete this secret.",
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )

    # Auto delete after 30 seconds
    await asyncio.sleep(30)
    try:
        await msg.delete()
    except:
        pass

# Handle "Inline" button
async def inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "**🧾 Here's your inline message preview\\!**\nOnly you can see this\\. 👀",
        parse_mode="MarkdownV2"
    )

# Handle "Reveal" button
async def reveal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "**😲 Secret Revealed:**\n> This is a hidden message\\!",
        parse_mode="MarkdownV2"
    )

# Handle "Delete" button
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Message deleted ✅", show_alert=False)
    try:
        await query.message.delete()
    except:
        pass

# Auto-load this plugin (no need to edit main.py)
def __load__(app):
    app.add_handler(CommandHandler("wishper", wspr))
    app.add_handler(CallbackQueryHandler(inline, pattern="^wishper_inline$"))
    app.add_handler(CallbackQueryHandler(reveal, pattern="^wishper_reveal$"))
    app.add_handler(CallbackQueryHandler(delete, pattern="^wishper_delete$"))
