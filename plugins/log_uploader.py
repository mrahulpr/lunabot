import os
import asyncio
from datetime import datetime

LOG_FILE = "bot.log"
LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID")
LOG_INTERVAL = int(os.environ.get("LOG_INTERVAL", 300))

sent_text = ""

def get_info():
    return {
        "name": "Log Sender 📄",
        "description": "Sends logs as plain text every few minutes."
    }

async def send_logs(app):
    global sent_text
    if not os.path.exists(LOG_FILE) or not LOG_CHAT_ID:
        return

    with open(LOG_FILE, "r") as f:
        data = f.read()

    new = data[len(sent_text):]
    if new.strip():
        sent_text = data
        message = new[-4000:]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            await app.bot.send_message(
                chat_id=LOG_CHAT_ID,
                text=f"🧾 *Log Update* `{timestamp}`\n\n```{message}```",
                parse_mode="Markdown"
            )
        except Exception as e:
            print("❌ Log send error:", e)

async def log_loop(app):
    while True:
        await send_logs(app)
        await asyncio.sleep(LOG_INTERVAL)

def setup(app):
    async def start_logs(app_):
        app_.create_task(log_loop(app_))
    app.post_init = start_logs
