from telegram import Update, InputFile
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from PIL import Image, ImageDraw, ImageFont
import io
from plugins.db import send_error_to_support

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # or custom

async def quotely(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ You must reply to a message to quote it.")
            return
        
        replied = update.message.reply_to_message
        text = replied.text or replied.caption or "⚠️ No text found"
        username = replied.from_user.full_name

        # Create image
        img = Image.new("RGB", (800, 200), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype(FONT_PATH, 28)
        draw.text((30, 40), f"{username}:", font=font, fill=(0, 0, 0))
        draw.text((30, 90), text, font=font, fill=(50, 50, 50))

        # Save image to memory
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        await update.message.reply_photo(photo=InputFile(img_bytes, filename="quote.png"))
    
    except Exception as e:
        await send_error_to_support(f"❌ Error in /q: {e}")
        await update.message.reply_text("⚠️ Failed to generate quote image.")

def setup(app):
    app.add_handler(CommandHandler("q", quotely))

def get_info():
    return {
        "name": "Quotely Image",
        "description": "Convert messages to quote-style images using /q"
    }

async def test():
    pass  # No DB needed for this one
