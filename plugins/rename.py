from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters, CommandHandler, ConversationHandler import os import time

State for conversation

WAITING_FOR_RENAME = 1

In-memory store to track which user wants to rename what

user_file_store = {}

async def start_rename(update: Update, context: ContextTypes.DEFAULT_TYPE): file = update.message.document or update.message.video or update.message.audio if not file: await update.message.reply_text("❌ Please send a document, video, or audio file to rename.") return

file_id = file.file_id
file_name = file.file_name or "Unnamed_File"

user_file_store[update.message.from_user.id] = {
    'file_id': file_id,
    'file_name': file_name,
    'file_type': file.mime_type
}

kb = [[InlineKeyboardButton("✏️ Rename", callback_data="rename_file")]]
await update.message.reply_text(
    f"📄 File: `{file_name}`",
    reply_markup=InlineKeyboardMarkup(kb),
    parse_mode='Markdown'
)

async def rename_button(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer()

user_id = query.from_user.id
if user_id not in user_file_store:
    await query.edit_message_text("❌ No file found to rename. Please resend your file.")
    return ConversationHandler.END

await query.edit_message_text("✏️ Send the new filename (without extension):")
return WAITING_FOR_RENAME

async def perform_rename(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id new_name = update.message.text.strip()

if user_id not in user_file_store:
    await update.message.reply_text("❌ No file found in memory. Please send your file again.")
    return ConversationHandler.END

file_data = user_file_store[user_id]
file = await context.bot.get_file(file_data['file_id'])

# Extract extension
old_name = file_data['file_name']
extension = os.path.splitext(old_name)[1] or ''
new_filename = new_name + extension
temp_path = f"temp/{user_id}_{int(time.time())}{extension}"

os.makedirs("temp", exist_ok=True)
await file.download_to_drive(temp_path)

await update.message.reply_document(
    document=InputFile(temp_path, filename=new_filename),
    caption=f"✅ Renamed to `{new_filename}`",
    parse_mode='Markdown'
)

os.remove(temp_path)
user_file_store.pop(user_id, None)
return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("❌ Rename cancelled.") return

