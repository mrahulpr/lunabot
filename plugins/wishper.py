import asyncio from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message, constants from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

SECRET_CACHE = {}  # user_id -> (message_id, text)

async def wishper(update: Update, context: ContextTypes.DEFAULT_TYPE): if update.message is None: return

user_id = update.effective_user.id

# Extract the secret message from inline command
args = context.args
if not args:
    return await update.message.reply_text("❌ *Usage:* `/wishper Your secret message`\nUse it via inline to stay hidden.", parse_mode=constants.ParseMode.MARKDOWN_V2)

secret_text = " ".join(args)

# Send interactive whisper with buttons
keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🔓 Reveal", callback_data=f"wishper_reveal:{user_id}"),
        InlineKeyboardButton("❌ Delete", callback_data=f"wishper_delete:{user_id}")
    ]
])
msg = await update.message.reply_text(
    "🔐 *Whisper Created\!*\nOnly *you* can reveal or delete this secret.",
    parse_mode=constants.ParseMode.MARKDOWN_V2,
    reply_markup=keyboard
)

# Store the secret
SECRET_CACHE[user_id] = (msg.message_id, secret_text)

# Auto-delete after 30 sec
await asyncio.sleep(30)
try:
    await msg.delete()
except:
    pass
if user_id in SECRET_CACHE and SECRET_CACHE[user_id][0] == msg.message_id:
    del SECRET_CACHE[user_id]

async def wishper_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query user_id = query.from_user.id await query.answer()

action, owner_id = query.data.split(":")
owner_id = int(owner_id)

if user_id != owner_id:
    return await query.answer("⚠️ This is not your secret!", show_alert=True)

if action == "wishper_reveal":
    if owner_id in SECRET_CACHE:
        _, text = SECRET_CACHE.pop(owner_id)
        await query.edit_message_text(f"💬 *Secret:* `{text}`", parse_mode=constants.ParseMode.MARKDOWN_V2)
    else:
        await query.edit_message_text("❗ Secret expired or already revealed.")

elif action == "wishper_delete":
    if owner_id in SECRET_CACHE:
        SECRET_CACHE.pop(owner_id)
    await query.message.delete()

def get_info(): return { "name": "Wishper 🤫", "description": "Send a secret whisper with buttons only you can reveal." }

def setup(app): app.add_handler(CommandHandler("wishper", wishper)) app.add_handler(CallbackQueryHandler(wishper_buttons, pattern=r"^wishper_(reveal|delete):\d+$"))

