import io
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from plugins.db import send_error_to_support

async def quote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.reply_to_message:
            await update.message.reply_text("⚠️ Reply to a message with /q to quote it.")
            return

        original = update.message.reply_to_message
        user = original.from_user.first_name
        text = original.text or original.caption

        if not text:
            await update.message.reply_text("⚠️ Cannot quote this type of message.")
            return

        # Create image
        width, height = 800, 400
        image = Image.new("RGB", (width, height), color=(40, 40, 40))
        draw = ImageDraw.Draw(image)

        # Use default font
        font = ImageFont.load_default()

        draw.text((30, 40), f"{user}:", fill="white", font=font)
        draw.text((30, 80), text, fill="lightgray", font=font)

        # Convert to WEBP and send
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP")
        buffer.seek(0)

        await update.message.reply_sticker(buffer)

    except Exception as e:
        await send_error_to_support(f"❌ Error in /q: {e}")
        await update.message.reply_text("⚠️ Failed to generate quote.")

def setup(app):
    app.add_handler(CommandHandler("q", quote_handler))

async def test():
    assert True

def get_info():
    return {"name": "Quotely", "description": "Create quote sticker from replied message."}
