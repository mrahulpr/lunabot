import aiohttp
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

G_TOKEN = os.getenv("G_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")  # e.g., "rahulxyz/mybot"
ALLOWED_USER_ID = int(os.getenv("OWNER_ID"))


async def stop_workflows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text(
            "🚫 You're not allowed to run this command\\.",
            parse_mode="MarkdownV2"
        )
        return

    keyboard = [
        [InlineKeyboardButton("✅ Confirm Stop", callback_data="confirm_stop_workflows")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚠️ Are you sure you want to stop all running workflows except the *latest one*\\?",
        reply_markup=reply_markup,
        parse_mode="MarkdownV2"
    )


async def confirm_stop_workflows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if user_id != ALLOWED_USER_ID:
        await query.answer("നീ എൻ്റെ മുതലാളി അല്ല 😜", show_alert=True)
        return

    await query.answer("Stopping workflows...")

    headers = {
        "Authorization": f"Bearer {G_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    url = f"https://api.github.com/repos/{REPO_NAME}/actions/runs"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            runs = [run for run in data.get("workflow_runs", []) if run["status"] == "in_progress"]

            if not runs:
                await query.edit_message_text(
                    "✅ No running workflows found\\.",
                    parse_mode="MarkdownV2"
                )
                return

            runs.sort(key=lambda x: x["created_at"], reverse=True)
            latest_run_id = runs[0]["id"]
            to_cancel = runs[1:]  # Skip latest

            count = 0
            for run in to_cancel:
                cancel_url = f"https://api.github.com/repos/{REPO_NAME}/actions/runs/{run['id']}/cancel"
                async with session.post(cancel_url, headers=headers) as cancel_response:
                    if cancel_response.status == 202:
                        count += 1

            await query.edit_message_text(
                f"🛑 Cancelled *{count}* old workflow\\(s\\)\\. Latest one \\(ID: `{latest_run_id}`\\) is still running\\.",
                parse_mode="MarkdownV2"
            )


def setup(app):
    app.add_handler(CommandHandler("stopworkflows", stop_workflows))
    app.add_handler(CallbackQueryHandler(confirm_stop_workflows, pattern="^confirm_stop_workflows$"))
