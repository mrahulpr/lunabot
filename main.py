import os
from telegram.ext import Updater
from plugins import load_plugins

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

updater = Updater(BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Load all plugins dynamically
load_plugins(dispatcher, updater.bot)

# Notify owner (on bot start)
updater.bot.send_message(chat_id=OWNER_ID, text="🚀 Bot restarted via GitHub Action!")

# Call any plugin-specific start code (like scheduled jobs)
updater.start_polling()
updater.idle()
