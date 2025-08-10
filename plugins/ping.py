# plugins/ping.py

import time
import asyncio
import speedtest
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# Ping command
async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    message = await update.message.reply_text("🏓 Pinging...")
    end_time = time.time()
    ping_ms = int((end_time - start_time) * 1000)

    keyboard = [
        [InlineKeyboardButton("🚀 Speed Test", callback_data="test_speed")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.edit_text(
        f"✅ *Pong!*\n📡 *Ping :* {ping_ms} ms",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# Callback for speed test
async def test_speed_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Initial "testing" message
    msg = await query.edit_message_text("🚀 Running speed test...\nPlease wait ⏳")

    # Animation loop while speedtest runs
    animation_task = asyncio.create_task(animate_loading(context, msg))

    # Run actual speedtest in separate thread (blocking)
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, run_speed_test)

    # Stop animation
    animation_task.cancel()

    # Show final results
    await query.edit_message_text(
        f"📊 *Speed Test Results*\n\n"
        f">• *🖥 Server  : {results['server']}*\n"
        f">• *📡 Ping    : {results['ping']} ms*\n"
        f">• *⬇ Download : {results['download']} Mbps*\n"
        f">• *⬆ Upload   : {results['upload']} Mbps*\n\n"
        f"[*©️ Webotz*](https://t.me/webotz)",
        parse_mode="MarkdownV2"
    )


# Animation function
async def animate_loading(context, msg):
    dots = [".", "..", "...", "...."]
    i = 0
    while True:
        await asyncio.sleep(0.5)
        try:
            await msg.edit_text(f"🚀 Running *speed test* {dots[i % len(dots)]}\n\n*Please wait *⏳.")
            i += 1
        except:
            break


async def test():
    # Nothing to test in this plugin; it's stateless and safe
    pass

# Actual speed test
def run_speed_test():
    st = speedtest.Speedtest()
    st.get_best_server()
    download = round(st.download() / 1_000_000, 2)  # Mbps
    upload = round(st.upload() / 1_000_000, 2)      # Mbps
    ping = round(st.results.ping, 2)
    server_name = st.results.server.get("name", "Unknown")
    return {
        "download": download,
        "upload": upload,
        "ping": ping,
        "server": server_name
    }

# Required plugin functions
def get_info():
    return {
        "name": "Ping & Speedtest",
        "description": "Checks ping and server's internet speed."
    }

def setup(app):
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CallbackQueryHandler(test_speed_callback, pattern="^test_speed$"))
def setup(app):
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CallbackQueryHandler(test_speed_callback, pattern="^test_speed$"))
