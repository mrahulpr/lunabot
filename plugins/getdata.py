import os
import json
from io import BytesIO
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = int(os.getenv("OWNER_ID"))
SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID"))

client = AsyncIOMotorClient(MONGO_URI)
db = client["telegram_bot"]

def setup(app):
    app.add_handler(CommandHandler("getdata", getdata_command))
    app.add_handler(CallbackQueryHandler(getdata_callback, pattern="^getdata:"))

# ----------- /getdata command -----------
async def getdata_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != SUPPORT_CHAT_ID:
        return await update.message.reply_text("❌ This command only works in the support chat.")

    keyboard = [[InlineKeyboardButton("📊 Get All Database Information", callback_data="getdata:menu")]]
    await update.message.reply_text(
        "🔍 Choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ----------- Callback Handler -----------
async def getdata_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split(":", 1)[1]
    await query.answer()

    if data == "menu":
        if user_id != OWNER_ID:
            return await query.edit_message_text("⚠️ Only the owner can access this menu.")
        return await show_collections_menu(query)

    elif data.startswith("collection:"):
        coll_name = data.split(":", 1)[1]
        collection = db[coll_name]
        docs = await collection.find({}).to_list(length=500)

        if not docs:
            return await query.edit_message_text(f"📂 *{coll_name}* collection is empty.", parse_mode="MarkdownV2")

        text = "\n\n".join(format_document(doc) for doc in docs)
        if len(text) < 4096:
            await query.edit_message_text(
                text=f"📄 *Data in `{coll_name}`:*\n\n{text}",
                parse_mode="MarkdownV2",
                reply_markup=get_navigation("menu")
            )
        else:
            file = InputFile(BytesIO(text.encode()), filename=f"{coll_name}_data.txt")
            await query.edit_message_text(
                f"📄 *Data in `{coll_name}` is too large. Sending as file:*",
                parse_mode="MarkdownV2",
                reply_markup=get_navigation("menu")
            )
            await query.message.reply_document(file)

    elif data == "menu":
        return await show_collections_menu(query)

    elif data == "close":
        return await query.delete_message()

# ----------- Format MongoDB Document -----------
def format_document(doc):
    doc = dict(doc)
    doc.pop("_id", None)
    parts = []
    for k, v in doc.items():
        if isinstance(v, datetime):
            v = v.isoformat()
        parts.append(f"*{k}*: `{str(v)}`")
    return "\n".join(parts)

# ----------- Show Collections Menu -----------
async def show_collections_menu(query):
    collections = await db.list_collection_names()
    if not collections:
        return await query.edit_message_text("⚠️ No collections found in the database.")

    # Arrange in rows of 3
    buttons = []
    row = []
    for name in collections:
        row.append(InlineKeyboardButton(name, callback_data=f"getdata:collection:{name}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("🔙 Back", callback_data="getdata:menu"),
        InlineKeyboardButton("❌ Close", callback_data="getdata:close"),
    ])

    await query.edit_message_text(
        "📚 *Select a collection:*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ----------- Navigation Buttons -----------
def get_navigation(back_to):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=f"getdata:{back_to}")],
        [InlineKeyboardButton("❌ Close", callback_data="getdata:close")]
    ])
