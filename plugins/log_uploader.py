import os
import asyncio
import logging
from telegram.ext import Application, CommandHandler, ContextTypes

LOG_FILE = "bot.log"
LAST_LINE_FILE = "last_log_line.txt"
LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", "0"))  # Set this in GitHub Secrets

# Set up logger if not already set
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not any(isinstance(h, logging.FileHandler) and h.baseFilename.endswith(LOG_FILE) for h in logger.handlers):
        handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

# Upload new log lines since last sent
async def upload_logs_task(app: Application):
    while True:
        await asyncio.sleep(600)  # Run every 10 minutes

        if not os.path.exists(LOG_FILE):
            continue

        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        last_index = 0
        if os.path.exists(LAST_LINE_FILE):
            try:
                with open(LAST_LINE_FILE, "r") as f:
                    last_index = int(f.read().strip())
            except:
                last_index = 0

        new_lines = lines[last_index:]
        if new_lines and LOG_CHAT_ID != 0:
            log_text = "".join(new_lines).strip()
            chunks = [log_text[i:i + 4000] for i in range(0, len(log_text), 4000)]

            for chunk in chunks:
                try:
                    await app.bot.send_message(LOG_CHAT_ID, f"📄 New Logs:\n\n<pre>{chunk}</pre>", parse_mode="HTML")
                except Exception as e:
                    print(f"❌ Failed to send log chunk: {e}")

            with open(LAST_LINE_FILE, "w") as f:
                f.write(str(len(lines)))

# Plugin setup
def setup(app: Application):
    setup_logger()

    # Start periodic log task after bot starts
    async def post_startup(app_: Application):
        app_.create_task(upload_logs_task(app_))
        logging.info("🚀 Log uploader task started.")

    app.post_init = post_startup

    # Manual command to send all logs now
    async def send_logs(update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not os.path.exists(LOG_FILE):
                await update.message.reply_text("📭 Log file not found.")
                return

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
