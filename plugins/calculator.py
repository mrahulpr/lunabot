from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

commands = ["calc"]

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("7", callback_data="7"), InlineKeyboardButton("8", callback_data="8"), InlineKeyboardButton("9", callback_data="9"), InlineKeyboardButton("/", callback_data="/")],
        [InlineKeyboardButton("4", callback_data="4"), InlineKeyboardButton("5", callback_data="5"), InlineKeyboardButton("6", callback_data="6"), InlineKeyboardButton("*", callback_data="*")],
        [InlineKeyboardButton("1", callback_data="1"), InlineKeyboardButton("2", callback_data="2"), InlineKeyboardButton("3", callback_data="3"), InlineKeyboardButton("-", callback_data="-")],
        [InlineKeyboardButton("0", callback_data="0"), InlineKeyboardButton(".", callback_data="."), InlineKeyboardButton("=", callback_data="="), InlineKeyboardButton("+", callback_data="+")],
        [InlineKeyboardButton("Clear", callback_data="C")]
    ]
    await update.message.reply_text("🧮 Calculator\nTap the buttons below:", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_data = context.user_data

    if "expression" not in user_data:
        user_data["expression"] = ""

    if data == "C":
        user_data["expression"] = ""
    elif data == "=":
        try:
            result = eval(user_data["expression"], {"__builtins__": {}})
            user_data["expression"] = str(result)
        except:
            user_data["expression"] = "Error"
    else:
        user_data["expression"] += data

    await query.edit_message_text(f"🧮 `{user_data['expression']}`", parse_mode="Markdown", reply_markup=query.message.reply_markup)