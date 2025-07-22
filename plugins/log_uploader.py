import os
import logging
from typing import Optional

from telegram.ext import Application, CommandHandler, ContextTypes

LOG_FILE = "bot.log"
_last_pos = 0  # in-memory per run

LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", "0"))           # set in GitHub secrets
LOG_INTERVAL_SECONDS = int(os.getenv("LOG_INTERVAL_SECONDS", "900"))  # default 15m


def _setup_file_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # avoid duplicate handlers
    for h in logger.handlers:
        if isinstance(h, logging.FileHandler) and h.baseFilename.endswith(LOG_FILE):
            return
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(fh)


async def _send_new_logs(context: ContextTypes.DEFAULT_TYPE) -> None:
    global _last_pos
    if LOG_CHAT_ID == 0 or not os.path.exists(LOG_FILE):
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            f.seek(_last_pos)
            new_data = f.read()
            _last_pos = f.tell()
    except Exception as e:
        print(f"[log_uploader] read error: {e}")
        return

    if not new_data.strip():
        return

    # chunk into safe-sized messages
    max_len = 3900  # a little margin below 4096
    for i in range(0, len(new_data), max_len):
        chunk = new_data[i : i + max_len]
        try:
            await context.bot.send_message(
                chat_id=LOG_CHAT_ID,
                text=f"📝 Log update:\n\n<pre>{chunk}</pre>",
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"[log_uploader] send error: {e}")


async def _send_full_logs(update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(LOG_FILE):
        await update.message.reply_text("📭 Log file not found.")
        return
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        data = f.read() or "📭 (empty)"
    max_len = 3900
    for i in range(0, len(data), max_len):
        chunk = data[i : i + max_len]
        await update.message.reply_text(
            f"📝 Full logs:\n\n<pre>{chunk}</pre>",
            parse_mode="HTML",
        )


def get_info():
    return {
        "name": "📤 Log Messenger",
        "description": "Sends new logs to a private chat at intervals.",
    }


def setup(app: Application):
    _setup_file_logger()

    # repeating job (starts when app starts polling)
    app.job_queue.run_repeating(_send_new_logs, interval=LOG_INTERVAL_SECONDS, first=10)

    # manual command
    app.add_handler(CommandHandler("sendlogs", _send_full_logs))
