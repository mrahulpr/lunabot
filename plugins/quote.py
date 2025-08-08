import os
import io
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from plugins.db import send_error_to_support


FONT_PATH = os.path.join("assets", "fonts", "DejaVuSans.ttf")


async def quotely(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ Please reply to a message to quote it.")
            return

        replied = update.message.reply_to_message
        text = replied.text or replied.caption

        if not text:
            await update.message.reply_text("⚠️ Cannot quote empty or non-text messages.")
            return

        username = replied.from_user.first_name or "Unknown"

        # Create image
        img = Image.new("RGB", (600, 300), color="#2f3136")
        draw = ImageDraw.Draw(img)

        font_text = ImageFont.truetype(FONT_PATH, 28)
        font_user = ImageFont.truetype(FONT_PATH, 24)

        draw.text((30, 40), text, font=font_text, fill="white")
        draw.text((30, 220), f"— {username}", font=font_user, fill="#999")

        # Crop to square (Telegram stickers are square-shaped by default)
        img = img.crop((0, 0, 300, 300))

        # Convert to .webp for sticker
        output = io.BytesIO()
        img.save(output, format="WEBP")
        output.name = "quote.webp"
        output.seek(0)

        await update.message.reply_sticker(sticker=output)

    except Exception as e:
        await send_error_to_support(f"❌ Error in /q: `{str(e)}`")
        await update.message.reply_text("⚠️ Failed to generate quote sticker.")


def get_info():
    return {
        "name": "Quotely",
        "description": "Turn replied messages into sticker-style quotes using /q"
    }


def setup(app):
    app.add_handler(CommandHandler("q", quotely))


async def test():
    # This will check that the font file exists and can be loaded
    try:
        ImageFont.truetype(FONT_PATH, 24)
    except Exception as e:
        raise RuntimeError(f"[quotely] Font error: {e}")
