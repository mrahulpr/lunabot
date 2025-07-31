import aiohttp
import os
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

G_TOKEN = os.getenv("G_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")
ALLOWED_USER_ID = int(os.getenv("OWNER_ID"))
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def send_error_to_support(error: Exception):
    if not SUPPORT_CHAT_ID or not BOT_TOKEN:
        return
    bot = Bot(BOT_TOKEN)
    error_text = (
        "❗️ *Plugin Error: stop_workflows*\n"
        f"`{str(error)}`\n\n"
        f"```{traceback.format_exc()}```"
    )
    try:
        await bot.send_message(chat_id=SUPPORT_CHAT_ID, text=error_text[:4000], parse_mode="MarkdownV2")
    except Exception:
        pass


async def stop_workflows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
    except Exception as e:
        await send_error_to_support(e)


async def confirm_stop_workflows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
    except Exception as e:
        await send_error_to_support(e)

async def test():
    # Nothing to test in this plugin; it's stateless and safe
    pass


def setup(app):
    app.add_handler(CommandHandler("stopworkflows", stop_workflows))
    app.add_handler(CallbackQueryHandler(confirm_stop_workflows, pattern="^confirm_stop_workflows$"))
