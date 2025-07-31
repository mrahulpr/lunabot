import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from .db import send_error_to_support  # Import your error handler

async def hack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Simulates a fake hacking sequence on the user being replied to.
    The animation is displayed within a MarkdownV2 code block for a terminal-like effect.
    """
    try:
        # Check if the command is a reply to a message.
        if not update.message.reply_to_message:
            return await update.message.reply_text(
                "⚠️ You must reply to someone's message to use this command\\.", 
                parse_mode="MarkdownV2"
            )

        target = update.message.reply_to_message.from_user
        bot = context.bot
        me = await bot.get_me()

        # Prevent the bot from "hacking" itself.
        if target.id == me.id:
            return await update.message.reply_text(
                "🤖 I don't hack myself\\.\\.\\. nice try 😂", 
                parse_mode="MarkdownV2"
            )
        
        # A fun check for the bot's owner.
        if target.id == int(context.bot_data.get("OWNER_ID", 0)):
            return await update.message.reply_text(
                "🫣 I will hack my owner\\.\\.\\. please don't tell him\\!", 
                parse_mode="MarkdownV2"
            )

        # Send the initial message, starting the code block.
        msg = await update.message.reply_text(
            "```\n> Initializing hack sequence...\n```", 
            parse_mode="MarkdownV2"
        )
        
        # Keep track of the last text to avoid "message is not modified" errors.
        last_text = msg.text

        # Animation frames. No character escaping is needed here because they
        # will be rendered inside the code block.
        animation = [
            "Scanning target...",
            "Target locked.",
            "Connecting to secured server...",
            "Bypassing firewall 1...",
            "Bypassing firewall 2...",
            "Bypassing firewall 3...",
            "Installing payload... 10% 🟩⬜⬜⬜⬜⬜⬜⬜⬜⬜",
            "Installing payload... 25% 🟩🟩⬜⬜⬜⬜⬜⬜⬜⬜",
            "Installing payload... 67% 🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜",
            "Installing payload... 95% 🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜",
            "Uploading payload...",
            "Finalizing connection...",
            "Generating exploit link...",
            "Target successfully hacked!",
        ]

        buffer = []
        for line in animation:
            buffer.append(line)
            # This creates the scrolling effect.
            if len(buffer) > 4:
                buffer.pop(0)

            # Construct the text to be displayed inside the code block.
            text_to_send = "```\n" + "\n".join(f"> {l}" for l in buffer) + "\n```"
            
            # Only edit the message if the content has changed.
            if text_to_send != last_text:
                try:
                    await msg.edit_text(text_to_send, parse_mode='MarkdownV2')
                    last_text = text_to_send
                except Exception:
                    # Silently ignore errors, like being rate-limited.
                    pass
            
            # Pause between frames.
            await asyncio.sleep(1.2)

        # Final message after the animation completes.
        # Note the escaped '.' characters for MarkdownV2.
        await msg.edit_text(
            "> Target compromised\\. Click below to access the panel\\.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🕵️ View Hacked Panel", url="[https://example.com/hacked](https://example.com/hacked)")]]
            ),
            parse_mode="MarkdownV2"
        )

    except Exception as e:
        import traceback
        await send_error_to_support(
            f"*❌ Error in hack plugin:*\n`{e}`\n```{traceback.format_exc()}```"
        )


async def hack_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback function for the help menu button."""
    try:
        query = update.callback_query
        await query.answer()
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="help")]]
        text = (
            "💻 *Hack Plugin*\n\n"
            "Simulates a fake hacking sequence as a prank\\.\n\n"
            "*Usage:*\n"
            "`/hack` – Reply to a user's message to initiate a fake hack\\."
        )
        await query.edit_message_text(
            text, 
            parse_mode="MarkdownV2", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        import traceback
        await send_error_to_support(
            f"*❌ Hack help button error:*\n`{e}`\n```{traceback.format_exc()}```"
        )


def get_info():
    """Returns plugin information for help menus."""
    return {
        "name": "Hack 💻",
        "description": "Simulates a fake hacking prank with animations. Works only as a reply."
    }


def setup(app):
    """Adds the command and callback handlers to the application."""
    app.add_handler(CommandHandler("hack", hack))
    app.add_handler(CallbackQueryHandler(hack_help_callback, pattern="^plugin::hack$"))
