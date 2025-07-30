import os
import json
import traceback
from io import BytesIO
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = int(os.getenv("OWNER_ID"))
SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID"))

client = AsyncIOMotorClient(MONGO_URI)
db = client["telegram_bot"]

# --------- Setup plugin ---------
def setup(app):
    app.add_handler(CommandHandler("getdata", getdata_command))
    app.add_handler(CallbackQueryHandler(getdata_callback, pattern="^getdata:"))

# --------- /getdata command ---------
async def getdata_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_chat.id != SUPPORT_CHAT_ID:
            return await update.message.reply_text("❌ This command only works in the support chat.")

        keyboard = [[InlineKeyboardButton("📊 Get All Database Information", callback_data="getdata:menu")]]
        await update.message.reply_text(
            "🔍 Choose an option:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await send_error_to_support(e)

# --------- Callback Handler ---------
async def getdata_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        user_id = query.from_user.id
        data = query.data

        if data == "getdata:menu":
            if user_id != OWNER_ID:
                return await query.edit_message_text("⚠️ Only the owner can access this menu.")
            return await show_collections_menu(query)

        elif data.startswith("getdata:collection:"):
            coll_name = data.split("getdata:collection:", 1)[1]
            collection = db[coll_name]
            docs = await collection.find({}).to_list(length=500)

            if not docs:
                return await query.edit_message_text(
                    f"📂 *{escape_md(coll_name)}* collection is empty.",
                    parse_mode="MarkdownV2",
                    reply_markup=get_navigation("menu")
                )

            text = "\n\n".join(format_document(doc) for doc in docs)
            if len(text) < 4096:
                await query.edit_message_text(
                    text=f"📄 *Data in `{escape_md(coll_name)}`:*\n\n{text}",
                    parse_mode="MarkdownV2",
                    reply_markup=get_navigation("menu")
                )
            else:
                file = InputFile(BytesIO(text.encode()), filename=f"{coll_name}_data.txt")
                await query.edit_message_text(
                    f"📄 *Data in `{escape_md(coll_name)}` is too large. Sending as file:*",
                    parse_mode="MarkdownV2",
                    reply_markup=get_navigation("menu")
                )
                await query.message.reply_document(file)

        elif data == "getdata:close":
            return await query.delete_message()

    except Exception as e:
        await send_error_to_support(e)

# --------- Format MongoDB Document ---------
def format_document(doc):
    doc = dict(doc)
    doc.pop("_id", None)
    parts = []
    for k, v in doc.items():
        if isinstance(v, datetime):
            v = v.isoformat()
        parts.append(f"*{escape_md(str(k))}*: `{escape_md(str(v))}`")
    return "\n".join(parts)

# --------- Show Collections Menu ---------
async def show_collections_menu(query):
    try:
        collections = await db.list_collection_names()
        if not collections:
            return await query.edit_message_text("⚠️ No collections found in the database.")

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
    except Exception as e:
        await send_error_to_support(e)

# --------- Navigation Buttons ---------
def get_navigation(back_to):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=f"getdata:{back_to}")],
        [InlineKeyboardButton("❌ Close", callback_data="getdata:close")]
    ])

# --------- MarkdownV2 Escape ---------
def escape_md(text: str) -> str:
    for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(char, f"\\{char}")
    return text

# --------- Send Error to Support ---------
async def send_error_to_support(error: Exception):
    try:
        tb = traceback.format_exc()
        await db.send_error_to_support(
            f"*❌ Error in /getdata plugin:*\n`{str(error)}`\n```{tb}```"
        )
    except:
        pass

# --------- Plugin Test Function ---------
async def test():
    try:
        await db.command("ping")
    except Exception as e:
        raise RuntimeError("MongoDB not connected") from e
