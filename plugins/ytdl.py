from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
import yt_dlp
import os
import asyncio
from uuid import uuid4

# Memory storage for user sessions
user_sessions = {}

async def ytdl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🔗 Usage: /ytdl <YouTube link>")
        return
    url = context.args[0]

    msg = await update.message.reply_animation(
        animation="https://i.gifer.com/ZKZg.gif",
        caption="🔍 Fetching video info...",
    )

    # Fetch available formats
    try:
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        await msg.edit_caption(f"❌ Failed to fetch info:\n<code>{str(e)}</code>", parse_mode="HTML")
        return

    user_sessions[update.effective_user.id] = {"info": info, "url": url}

    # Create format selection buttons
    buttons = []
    formats_seen = set()
    for f in info.get('formats', []):
        ext = f.get('ext')
        if f.get('filesize') and f.get('format_note') and f.get('vcodec') != 'none':
            tag = f"{f['format_id']}|video"
            label = f"🎥 {f['format_note']} {ext.upper()}"
        elif f.get('filesize') and f.get('acodec') != 'none' and f.get('vcodec') == 'none':
            tag = f"{f['format_id']}|audio"
            kbps = int(f.get('abr', 0))
            label = f"🎧 {kbps}kbps {ext.upper()}"
        else:
            continue
        if label not in formats_seen:
            buttons.append([InlineKeyboardButton(label, callback_data=f"ytdl_dl|{tag}")])
            formats_seen.add(label)

    if not buttons:
        await msg.edit_caption("❌ No downloadable formats found.")
        return

    await msg.edit_caption("🔽 Choose a format to download:", reply_markup=InlineKeyboardMarkup(buttons))


async def ytdl_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_sessions:
        await query.edit_message_text("Session expired. Send the link again using /ytdl <link>")
        return

    info = user_sessions[user_id]["info"]
    url = user_sessions[user_id]["url"]
    format_id, typ = query.data.split('|')[1:]

    file_id = str(uuid4())
    temp_file = f"ytdl_{file_id}.{'mp4' if typ == 'video' else 'mp3'}"

    await query.edit_message_text("⬇️ Downloading...")

    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '').strip()
            asyncio.create_task(query.edit_message_text(f"📥 Downloading: {percent}"))
        elif d['status'] == 'finished':
            asyncio.create_task(query.edit_message_text("📤 Uploading..."))

    ydl_opts = {
        'format': format_id,
        'outtmpl': temp_file,
        'progress_hooks': [progress_hook],
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        await query.edit_message_text(f"❌ Error:\n<code>{str(e)}</code>", parse_mode="HTML")
        return

    caption = f"<b>{info.get('title', 'No Title')}</b>\n<a href='{url}'>📺 YouTube Link</a>"
    caption = caption[:1024]  # Telegram limit

    try:
        if typ == "video":
            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=open(temp_file, 'rb'),
                caption=caption,
                parse_mode="HTML",
                reply_to_message_id=query.message.message_id,
            )
        elif typ == "audio":
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=open(temp_file, 'rb'),
                caption=caption,
                parse_mode="HTML",
                reply_to_message_id=query.message.message_id,
            )
    except Exception as e:
        await query.edit_message_text(f"❌ Upload failed:\n<code>{str(e)}</code>", parse_mode="HTML")
        return
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    del user_sessions[user_id]


def get_info():
    return {
        "name": "YouTube Downloader",
        "description": "Downloads YouTube videos and audio",
        "hidden": True  # Don't add to help
    }

def setup(application):
    application.add_handler(CommandHandler("ytdl", ytdl_command))
    application.add_handler(CallbackQueryHandler(ytdl_button, pattern="^ytdl_dl"))
