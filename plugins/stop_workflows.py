import aiohttp
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import os

GITHUB_TOKEN = os.getenv("G_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")  # e.g., "rahulxyz/mybot"
ALLOWED_USER_ID = int(os.getenv("OWNER_ID"))


async def stop_workflows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("🚫 You're not allowed to run this command.")
        return

    headers = {
        "Authorization": f"Bearer {G_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    url = f"https://api.github.com/repos/{REPO_NAME}/actions/runs"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            running = [run for run in data.get("workflow_runs", []) if run["status"] == "in_progress"]

            if not running:
                await update.message.reply_text("✅ No running workflows found.")
                return

            count = 0
            for run in running:
                run_id = run["id"]
                cancel_url = f"https://api.github.com/repos/{REPO_NAME}/actions/runs/{run_id}/cancel"
                async with session.post(cancel_url, headers=headers) as cancel_response:
                    if cancel_response.status == 202:
                        count += 1

            await update.message.reply_text(f"🛑 Cancelled {count} running workflow(s).")

def setup(app):
    app.add_handler(CommandHandler("stopworkflows", stop_workflows))
