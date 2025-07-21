def setup(app: Application):
    setup_logger()

    async def post_startup(app_: Application):
        app_.create_task(upload_logs_task(app_))

    app.post_init = post_startup

    # Optional: manual logs command
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
