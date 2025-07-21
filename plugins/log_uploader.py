import os
import logging
from telegram.ext import ContextTypes, Application, CommandHandler
import asyncio
from dotenv import load_dotenv

load_dotenv()

LOG_FILE = "bot.log"
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")  # e.g. -1001234567890
LOG_INTERVAL = int(os.getenv("LOG_INTERVAL_SECONDS", 900))  # Default: 15 min

_last_sent_position = 0  # Will reset on each new GitHub run


def get_info():
    return {
        "name": "📤 Auto Log Messenger",
        "description": "Sends new logs as text messages to a private channel/group at regular intervals."
    }


async def upload_logs_task(app: Application):
    global _last_sent_position
    await app.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"📢 Log Messenger started. Interval: {LOG_INTERVAL} seconds.")

    while True:
        await asyncio.sleep(LOG_INTERVAL)

        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                f.seek(_last_sent_position)
                new_lines = f.read()
                _last_sent_position = f.tell()

                if new_lines.strip():
                    # Break message into chunks of 4000 characters (Telegram limit)
                    chunks = [new_lines[i:i + 4000] for i in range(0, len(new_lines), 4000)]
                    for chunk in chunks:
                        await app.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"📝 Log Update:\n\n<pre>{chunk}</pre>", parse_mode="HTML")

        except Exception as e:
            print(f"[LOG MESSENGER ERROR] {e}")


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == LOG_FILE for h in logger.handlers):
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def setup(app: Application):
    setup_logger()
    app.create_task(upload_logs_task(app))

    # Optional command for testing logs manually
    async def send_logs(update, context: ContextTypes.DEFAULT_TYPE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = f.read()
                if not logs.strip():
                    await update.message.reply_text("📭 No logs yet.")
                    return
                chunks = [logs[i:i + 4000] for i in range(0, len(logs), 4000)]
                for chunk in chunks:
                    await update.message.reply_text(f"📝 Full Logs:\n\n<pre>{chunk}</pre>", parse_mode="HTML")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Failed to send logs: {e}")

    app.add_handler(CommandHandler("sendlogs", send_logs))
