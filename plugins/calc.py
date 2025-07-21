from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

commands = ['calc']

def build_keyboard(expression=""):
    keys = [
        ["7", "8", "9", "/"],
        ["4", "5", "6", "*"],
        ["1", "2", "3", "-"],
        ["0", ".", "=", "+"],
        ["C"]
    ]
    keyboard = [
        [InlineKeyboardButton(text=key, callback_data=f"calc:{expression + key}") for key in row]
        for row in keys
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧮 Calculator", reply_markup=build_keyboard())

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.replace("calc:", "")
    await query.answer()
    if data.endswith("="):
        try:
            result = str(eval(data[:-1]))
        except:
            result = "Error"
        await query.edit_message_text(f"Result: {result}", reply_markup=build_keyboard())
    elif data.endswith("C"):
        await query.edit_message_text("🧮 Calculator", reply_markup=build_keyboard())
    else:
        await query.edit_message_text(data, reply_markup=build_keyboard(data))
