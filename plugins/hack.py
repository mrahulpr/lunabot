import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# Extended animation steps
HACK_STEPS = [
    "🔍 Scanning open ports on target...",
    "🔎 Found vulnerable service: `SSH v1.2` on port 22",
    "🧠 Exploiting known CVE-2022-XXXX vulnerability...",
    "📶 Bypassing firewall rules using packet fragmentation...",
    "🛡️ Anti-virus evasion successful.",
    "🔓 Brute-forcing credentials using RockYou.txt...",
    "🔐 Credentials found: `admin:shadowrealm`",
    "🧬 Decrypting hashed passwords...",
    "🧩 Rainbow tables applied... matches found!",
    "📂 Gaining shell access...",
    "📡 Elevating privileges with kernel exploit...",
    "📊 System information gathered: Linux x64, 32GB RAM, 8-core CPU",
    "📁 Reading `/etc/shadow`...",
    "🗃️ Backdooring SSH for persistent access...",
    "🚪 Opening reverse shell to attacker machine...",
    "📞 Reverse shell connected! Terminal access granted.",
    "🔍 Sniffing active sessions...",
    "👤 User 'root' currently active on TTY1.",
    "🗝️ Session hijack successful. You are now 'root'.",
    "🧾 Listing files in home directory...",
    "📚 Found `bank_details.txt`, `wallet_keys.json`, `secrets.env`",
    "📤 Uploading files to remote server...",
    "🌐 Connected to dark web marketplace...",
    "📦 Packaging stolen data...",
    "🪙 Converting data to Monero for anonymity...",
    "🧊 Using bulletproof proxies to hide trails...",
    "🛰️ Uploading via encrypted satellite uplink...",
    "💣 Planting self-destruct cronjob...",
    "🧹 Deleting bash history...",
    "♻️ Removing logs from `/var/log/auth.log`",
    "🧼 Secure wiping disk sectors with DoD 5220.22-M method...",
    "💾 Installing ransomware: `CyberFang v9.1`",
    "🔐 Encrypting user files...",
    "🧱 Lock screen activated with demand note...",
    "💀 Injecting trojan into startup scripts...",
    "🧬 Spoofing MAC address and routing via 13 proxies...",
    "📍 Tracing system location... masked via 3 VPN layers",
    "🕵️‍♂️ Observing webcam & microphone status...",
    "📸 Snapshot captured — image saved to dark web profile.",
    "📡 Broadcasting attack telemetry to darknet nodes...",
    "📲 Sending spoofed SMS from target's number...",
    "📥 Receiving Bitcoin payment from blackmail demand...",
    "🔁 Repeating attack on linked network devices...",
    "🔓 IoT device accessed: Smart Fridge — now mining crypto 🍦",
    "🔁 Connecting to corporate VPN...",
    "📁 Accessing internal Git repositories...",
    "🧾 Source code exfiltrated: `ProjectFalcon` and `ZeroDayVault`",
    "📩 Emailing secrets to encrypted ProtonMail address...",
    "⏳ Spoofing timestamps to bypass forensics...",
    "📉 Manipulating target’s bank transactions...",
    "🧨 Launching fake tax fraud alert to mislead authorities...",
    "🔍 Removing traces using custom rootkit...",
    "🔕 Triggering fake system update to cover exit...",
    "📡 Finalizing all data transmission...",
    "💽 Creating full disk image backup...",
    "🔃 Upload complete. Verifying file hash...",
    "✅ SHA256 Match! Data integrity confirmed.",
    "🚨 ALERT: Unexpected admin login detected... Spoofing response...",
    "📉 Throttling connection to avoid detection...",
    "📅 Scheduling deepfake attack for future deployment...",
    "🧑‍💻 ChatGPT.dll injected successfully. Neural AI unlocked 😈",
    "🤖 Gaining control over connected Alexa devices...",
    "🎙️ Target's microphone is now live...",
    "🔎 Analyzing speech patterns...",
    "🧠 Training deep model on user behavior...",
    "🎯 Simulated user profile complete. Total control established.",
    "💰 Selling stolen data to anonymous buyers...",
    "📈 Darknet Wallet: +4.78 BTC received.",
    "💼 Hack operation declared SUCCESSFUL."
]

# Dynamic loading bar animations
LOADING_FRAMES = [
    "▌▒░ Loading ░▒▌",
    "▓▒░ Initializing ░▒▓",
    "█▒░ Executing ░▒█",
    "▌▒░ Breaching ░▒▌",
    "▓▒░ Uploading ░▒▓",
    "█▒░ Finalizing ░▒█"
]

# /hack command
async def hack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = " ".join(context.args) if context.args else "target system"
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    msg = await update.message.reply_text(f"🛠️ Initiating ultra hack on *{target}*...\n", parse_mode="Markdown")

    for step in HACK_STEPS:
        frame = random.choice(LOADING_FRAMES)
        await asyncio.sleep(random.uniform(0.8, 1.4))
        try:
            await msg.edit_text(f"{frame}\n\n{step}")
        except:
            pass  # Ignore errors due to message edit limits

    await asyncio.sleep(1.5)
    await msg.edit_text(f"🎯 *{target}* has been completely hacked!\nYour digital soul is now mine. 💀", parse_mode="Markdown")

# Help menu
async def hack_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="help")]]
    text = (
        "💀 *Hack Plugin*\n\n"
        "This is a simulation of a hacking sequence with detailed animations.\n"
        "No real systems are harmed. 😄\n\n"
        "*Usage:*\n"
        "`/hack NASA` or `/hack friend123`"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# Plugin info
def get_info():
    return {
        "name": "Hack 💀",
        "description": "Ultra-realistic hacking simulation with animations."
    }

# Register handlers
def setup(app):
    app.add_handler(CommandHandler("hack", hack))
    app.add_handler(CallbackQueryHandler(hack_help_callback, pattern="^plugin_hack$"))
