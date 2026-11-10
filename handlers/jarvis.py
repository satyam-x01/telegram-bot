import os
import random
import string
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import db
from utils import escape_md

def get_apk_path() -> str | None:
    """Find local APK file path"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base_dir, "private-agent-main", "build", "app", "outputs", "flutter-apk", "app-debug.apk"),
        os.path.join(base_dir, "private-agent-main", "build", "app", "outputs", "flutter-apk", "app-release.apk"),
        os.path.join(base_dir, "apk", "app-release.apk"),
        os.path.join(base_dir, "apk", "app-debug.apk"),
        os.path.join(base_dir, "app-release.apk")
    ]
    for path in candidates:
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    return None

def get_exe_path() -> str | None:
    """Find local PC EXE file path"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base_dir, "pcexe", "MARK-L.exe"),
        r"C:\Users\jjadh\Documents\teligram music bot\pcexe\MARK-L.exe",
        os.path.join(base_dir, "private-agent-main", "pc_control_pc", "MARK-L.exe")
    ]
    for path in candidates:
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    return None

async def send_jarvis_exe_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send PC Executable document directly via Telegram"""
    chat_id = update.effective_chat.id
    exe_path = get_exe_path()

    if not exe_path:
        return

    file_size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    filename = os.path.basename(exe_path)
    caption = (
        f"💻 *Jarvis PC Agent Remote Executable* (`{filename}`)\n"
        f"📦 *File Size:* `{file_size_mb:.1f} MB`\n\n"
        f"🖥️ Run this executable on your Windows PC to pair with your Mobile & Telegram Bot!"
    )

    status_msg = None
    try:
        if update.message:
            status_msg = await update.message.reply_text("⏳ *Sending Jarvis PC Executable file...*", parse_mode="Markdown")
        elif update.callback_query:
            status_msg = await update.callback_query.message.reply_text("⏳ *Sending Jarvis PC Executable file...*", parse_mode="Markdown")

        with open(exe_path, "rb") as exe_file:
            await context.bot.send_document(
                chat_id=chat_id,
                document=exe_file,
                filename=filename,
                caption=caption,
                parse_mode="Markdown"
            )
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
    except Exception as e:
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
        print(f"Notice: Failed to upload EXE file directly: {e}")
        owner = escape_md(config.OWNER_USERNAME) if hasattr(config, "OWNER_USERNAME") else "@s2u_007"
        fallback_msg = (
            f"💻 *JARVIS PC AGENT EXECUTABLE* (`{filename}`)\n\n"
            f"📦 *File Size:* `{file_size_mb:.1f} MB`\n\n"
            f"⚠️ *File Transfer Notice:* Telegram Bot API limits direct bot uploads to 50MB (`{filename}` is `{file_size_mb:.1f} MB`).\n"
            f"💬 *Contact Owner:* Please contact {owner} for the direct file download link!"
        )
        if update.message:
            await update.message.reply_text(fallback_msg, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.reply_text(fallback_msg, parse_mode="Markdown")

async def send_jarvis_apk_file(update: Update, context: ContextTypes.DEFAULT_TYPE, pair_code: str = ""):
    """Send APK document directly via Telegram"""
    chat_id = update.effective_chat.id
    apk_path = get_apk_path()

    if not apk_path:
        return

    file_size_mb = os.path.getsize(apk_path) / (1024 * 1024)
    caption = (
        f"📱 *Jarvis Mobile Remote Agent APK*\n"
        f"📦 *File Size:* `{file_size_mb:.1f} MB`\n"
        f"🔑 *Pair Code:* `{pair_code}`\n\n"
        f"📥 Install this APK on your Android phone and enter pair code to connect!"
    )

    status_msg = None
    try:
        if update.message:
            status_msg = await update.message.reply_text("⏳ *Sending Jarvis Mobile APK file...*", parse_mode="Markdown")
        elif update.callback_query:
            status_msg = await update.callback_query.message.reply_text("⏳ *Sending Jarvis Mobile APK file...*", parse_mode="Markdown")

        with open(apk_path, "rb") as apk_file:
            await context.bot.send_document(
                chat_id=chat_id,
                document=apk_file,
                filename="Jarvis-Mobile-Agent.apk",
                caption=caption,
                parse_mode="Markdown"
            )
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
    except Exception as e:
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
        print(f"Notice: Failed to upload APK file directly: {e}")
        owner = escape_md(config.OWNER_USERNAME) if hasattr(config, "OWNER_USERNAME") else "@s2u_007"
        fallback_msg = (
            f"📱 *JARVIS MOBILE APK FILE* (`{file_size_mb:.1f} MB`)\n\n"
            f"⚠️ *File Transfer Notice:* Telegram Bot API limits direct bot uploads to 50MB.\n"
            f"💬 *Contact Owner:* Please contact {owner} to get the direct file link!"
        )
        if update.message:
            await update.message.reply_text(fallback_msg, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.reply_text(fallback_msg, parse_mode="Markdown")


OFFLINE_COMMANDS_TEXT = """
🤖 *100+ FAST OFFLINE SHORTCUT COMMANDS (NO API KEY NEEDED!)* ⚡

📱 *1. APP LAUNCHERS (30+ Apps)*
• `open youtube` | `open whatsapp` | `open spotify`
• `open instagram` | `open telegram` | `open chrome`
• `open camera` | `open photos` | `open gallery`
• `open settings` | `open contacts` | `open phone`
• `open gmail` | `open maps` | `open playstore`
• `open clock` | `open calculator` | `open calendar`
• `open files` | `open notes` | `open netflix`
• `open facebook` | `open twitter` | `open snapchat`
• `open linkedin` | `open zoom` | `open drive`

🔋 *2. DEVICE CONTROLS & TOGGLES (20+ Commands)*
• `torch on` / `flashlight on` | `torch off`
• `wifi on` | `wifi off` | `bluetooth on` | `bluetooth off`
• `mute` / `silent` | `unmute` / `normal` | `dnd on`
• `volume up` | `volume down` | `max volume`
• `brightness up` | `brightness down`
• `take screenshot` | `lock screen` | `battery status`
• `reboot phone` | `auto rotate on`

🎵 *3. MEDIA & PLAYBACK CONTROLS (15+ Commands)*
• `play` / `resume` | `pause` / `stop`
• `next song` | `previous song`
• `seek forward` | `seek backward`
• `music volume up` | `music volume down`

📞 *4. CALLS, SMS & WHATSAPP (15+ Commands)*
• `call <contact name>` (e.g. `call Mom`)
• `sms <name> <message>` (e.g. `sms John Hi there`)
• `whatsapp <name> <message>` (e.g. `whatsapp Alex Meeting at 5`)
• `open calls` | `open messages`

🛠️ *5. UTILITIES & FAST SEARCH (20+ Commands)*
• `search <query>` (e.g. `search best laptops 2026`)
• `youtube search <query>` (e.g. `youtube search phonk music`)
• `navigate to <location>` (e.g. `navigate to Taj Mahal`)
• `calculate <expression>` (e.g. `calculate 25 * 4`)
• `set alarm <time>` | `set timer <minutes>`
• `check storage` | `open qr scanner` | `copy clipboard`

💡 *Note:* All 100+ commands run 100% offline at ultra-fast speeds! Add an API Key in Jarvis Settings to unlock infinite AI capabilities on top of these commands.
"""

async def jarvis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main /jarvis command handler - Generates unique dynamic pair code & setup UI"""
    user_id = update.effective_user.id
    pair_code = db.generate_jarvis_code(user_id)
    session = db.get_jarvis_session(user_id)
    is_active = db.is_nova_session_active(user_id)

    if is_active:
        rem_sec = db.get_nova_session_remaining(user_id)
        status_str = f"🟢 LIVE (ACTIVE - {rem_sec//60}m {rem_sec%60}s remaining)"
    else:
        status_str = "🟢 CONNECTED" if session and session.get("status") == "connected" else "🔴 UNPAIRED"
    
    device_str = escape_md(session.get("device_name", "NOVA Private Agent Mobile")) if session else "NOVA Mobile"

    text = (
        f"🤖 *NOVA PRIVATE AGENT & JARVIS REMOTE HUB* ⚡\n\n"
        f"Control your Android Mobile remotely from this Telegram bot!\n\n"
        f"🔑 *YOUR UNIQUE PAIR CODE:* `{pair_code}`\n"
        f"📡 *Connection Status:* `{status_str}` ({device_str})\n\n"
        f"📌 *Quick Setup Guide:*\n"
        f"1️⃣ Open *NOVA App* on your phone & enter pair code: `{pair_code}`\n"
        f"2️⃣ Click *Start Nova* button below or send `/startnova` to activate 5-minute remote control!\n"
        f"3️⃣ Send commands like *Open YouTube*, *Take Screenshot*, *Volume Up* directly in chat!"
    )

    keyboard = [
        [
            InlineKeyboardButton("🚀 Start Nova (5 Min Control)", callback_data="btn_start_nova"),
            InlineKeyboardButton("📱 Download Mobile APK", callback_data="btn_jarvis_apk")
        ],
        [
            InlineKeyboardButton(f"🔗 Connect Code: {pair_code}", callback_data=f"btn_jarvis_connect_{pair_code}"),
            InlineKeyboardButton("🔄 New Pair Code", callback_data="btn_jarvis_recode")
        ],
        [
            InlineKeyboardButton("📜 100+ Remote Commands", callback_data="btn_jarvis_help"),
            InlineKeyboardButton("📡 Check Status", callback_data="btn_jarvis_status")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        await send_jarvis_apk_file(update, context, pair_code)
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def startnova_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /startnova - Activates 5-minute active NOVA Mobile Agent Remote Session."""
    user_id = update.effective_user.id
    db.start_nova_session(user_id, duration_seconds=300)
    rem_sec = db.get_nova_session_remaining(user_id)

    text = (
        f"🚀 *NOVA PRIVATE AGENT ACTIVATED!* ⚡\n\n"
        f"📱 *Device Status:* 🟢 CONNECTED & LIVE\n"
        f"⏳ *Active Duration:* `5 Minutes` (Expires in {rem_sec} seconds)\n\n"
        f"🎯 *Any message you send now will execute directly on your mobile app!*\n\n"
        f"📌 *Try these sample commands:*\n"
        f"• `open youtube` — Opens YouTube App on phone\n"
        f"• `open chrome` — Opens Chrome Browser\n"
        f"• `open instagram` — Opens Instagram\n"
        f"• `take screenshot` — Captures screen\n"
        f"• `volume up` / `mute` — Controls audio\n"
        f"• `torch on` — Turns on flashlight"
    )

    keyboard = [
        [
            InlineKeyboardButton("📜 100+ Remote Commands", callback_data="btn_jarvis_help"),
            InlineKeyboardButton("🛑 Stop Session", callback_data="btn_stop_nova")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def connectjarvis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify or complete Jarvis device pairing: /connectjarvis <code>"""
    user_id = update.effective_user.id
    input_code = context.args[0].strip() if context.args else None

    if not input_code:
        session = db.get_jarvis_session(user_id)
        if session and session.get("pair_code"):
            input_code = session.get("pair_code")
        else:
            await update.message.reply_text(
                "❌ *Please provide your Jarvis Pair Code!*\n"
                "Example: `/connectjarvis JRV-839210`\n\n"
                "Get your pair code by sending `/jarvis`.",
                parse_mode="Markdown"
            )
            return

    # Attempt connection pairing
    success = db.connect_jarvis_code(user_id, input_code, device_name="Jarvis Mobile AI / PC Node")

    if success:
        session = db.get_jarvis_session(user_id)
        pair_code = session.get("pair_code") if session else input_code
        text = (
            f"✅ *JARVIS AGENT CONNECTED SUCCESSFULLY!* ⚡\n\n"
            f"🔑 *Pair Code:* `{pair_code}`\n"
            f"📱 *Connected Device:* `Jarvis Mobile AI Agent / PC Node`\n"
            f"📡 *Status:* 🟢 ACTIVE & LISTENING\n\n"
            f"🎯 *Ready to execute commands!* Try sending:\n"
            f"• `open youtube` or `open whatsapp`\n"
            f"• `take screenshot` or `torch on`\n"
            f"• `volume up` or `battery status`\n"
            f"• `search best movies 2026`"
        )
        keyboard = [[InlineKeyboardButton("📜 View 100+ Commands", callback_data="btn_jarvis_help")], [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        text = (
            f"❌ *INVALID OR UNPAIRED JARVIS CODE!* 🔴\n\n"
            f"The code `{escape_md(input_code)}` could not be verified or has expired.\n\n"
            f"💡 *Troubleshooting:*\n"
            f"1️⃣ Make sure you generated a code using `/jarvis`.\n"
            f"2️⃣ Ensure the code is typed in Jarvis Mobile APK / PC EXE.\n"
            f"3️⃣ Generate a fresh code anytime using `/jarvis`."
        )
        keyboard = [[InlineKeyboardButton("🔑 Get Fresh Pair Code", callback_data="btn_jarvis_recode")]]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def jarvis_apk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download Jarvis Mobile APK"""
    user_id = update.effective_user.id
    pair_code = db.generate_jarvis_code(user_id)

    text = (
        f"📱 *JARVIS MOBILE AGENT APK DOWNLOAD* 🤖\n\n"
        f"Download the official Jarvis Mobile Android APK (`PrivateAgent-universal.apk`).\n\n"
        f"🔑 *YOUR DYNAMIC PAIR CODE:* `{pair_code}`\n\n"
        f"📥 *Download Link:* [Jarvis Mobile Agent APK](https://github.com/orailnoor/private-agent/releases/latest)\n\n"
        f"⚙️ *Installation Steps:*\n"
        f"1. Install the APK on your Android device (Android 8.0+ supported).\n"
        f"2. Enable **Accessibility Service** ('PrivateAgent Screen Control').\n"
        f"3. Enter Pair Code `{pair_code}` in Settings.\n"
        f"4. Confirm connection in Telegram with `/connectjarvis {pair_code}`."
    )
    keyboard = [
        [InlineKeyboardButton("📥 Download APK Direct", url="https://github.com/orailnoor/private-agent/releases/latest")],
        [InlineKeyboardButton("🔗 Connect Code", callback_data=f"btn_jarvis_connect_{pair_code}")],
        [InlineKeyboardButton("🔙 Back to Jarvis Menu", callback_data="btn_jarvis_menu")]
    ]
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    await send_jarvis_apk_file(update, context, pair_code)

async def jarvis_exe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download Jarvis PC Server Executable"""
    exe_path = get_exe_path()
    size_str = f"{os.path.getsize(exe_path)/(1024*1024):.1f} MB" if exe_path else "178.5 MB"
    filename = os.path.basename(exe_path) if exe_path else "MARK-L.exe"

    text = (
        f"💻 *JARVIS PC CONTROL EXECUTABLE SERVER* 🖥️\n\n"
        f"Control your Windows / Mac PC remotely via QR Scanner or Telegram!\n\n"
        f"📌 *PC Executable File:* `{filename}` (Size: `{size_str}`)\n"
        f"📁 *Server Location:* `C:\\Users\\jjadh\\Documents\\teligram music bot\\pcexe\\{filename}`\n\n"
        f"📌 *Features:*\n"
        f"• QR Code scanning pairing with Mobile Jarvis APK\n"
        f"• Remote Mouse, Keyboard, Xbox controller simulation\n"
        f"• System volume, Browser launching & PC Lock tasks\n\n"
        f"▶️ *Run on PC:* Double-click `{filename}` in `pcexe/` folder or run `python nova_pc_server.py` in `private-agent-main/pc_control_pc/`!"
    )
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Jarvis Menu", callback_data="btn_jarvis_menu")]
    ]
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    await send_jarvis_exe_file(update, context)

async def jarvis_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List 100+ Offline Shortcut Commands"""
    keyboard = [[InlineKeyboardButton("🔙 Back to Jarvis Menu", callback_data="btn_jarvis_menu")]]
    if update.message:
        await update.message.reply_text(OFFLINE_COMMANDS_TEXT, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text(OFFLINE_COMMANDS_TEXT, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def jarvisstatus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check Jarvis Connection Status"""
    user_id = update.effective_user.id
    session = db.get_jarvis_session(user_id)
    if session and session.get("status") == "connected":
        msg = (
            f"🟢 *JARVIS DEVICE CONNECTION STATUS: CONNECTED* ⚡\n\n"
            f"📱 *Connected Device:* `{escape_md(session.get('device_name', 'Jarvis Mobile / PC'))}`\n"
            f"🔑 *Active Pair Code:* `{session.get('pair_code')}`\n"
            f"📡 *State:* Ready for remote actions!\n\n"
            f"💡 Try typing commands like `open youtube`, `take screenshot`, `torch on`."
        )
    else:
        code = session.get("pair_code") if session else db.generate_jarvis_code(user_id)
        msg = (
            f"🔴 *JARVIS DEVICE CONNECTION STATUS: UNPAIRED* \n\n"
            f"🔑 *Active Pair Code:* `{code}`\n\n"
            f"📌 *How to connect:*\n"
            f"1. Open Mobile Jarvis App or PC EXE.\n"
            f"2. Enter pair code `{code}`.\n"
            f"3. Send `/connectjarvis {code}` in this bot to confirm connection!"
        )
    keyboard = [[InlineKeyboardButton("📜 View Commands", callback_data="btn_jarvis_help"), InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def jarvis_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all Jarvis inline keyboard callback queries"""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data in ["btn_jarvis_menu", "btn_jarvis_main"]:
        await jarvis_command(update, context)
    elif data == "btn_start_nova":
        await startnova_command(update, context)
    elif data == "btn_stop_nova":
        user_id = query.from_user.id
        db.disconnect_jarvis(user_id)
        await query.message.reply_text("🛑 *NOVA 5-Minute Remote Session Stopped.*", parse_mode="Markdown")
        await jarvis_command(update, context)
    elif data == "btn_jarvis_apk":
        await jarvis_apk_command(update, context)
    elif data == "btn_jarvis_exe":
        await jarvis_exe_command(update, context)
    elif data == "btn_jarvis_help":
        await jarvis_help_command(update, context)
    elif data == "btn_jarvis_recode":
        user_id = query.from_user.id
        new_code = db.generate_jarvis_code(user_id)
        await query.message.reply_text(f"🔑 *Fresh Pair Code Generated:* `{new_code}`\n\nEnter this code in Jarvis APK/EXE and send `/connectjarvis {new_code}`.", parse_mode="Markdown")
        await jarvis_command(update, context)
    elif data == "btn_jarvis_status":
        await jarvisstatus_command(update, context)
    elif data.startswith("btn_jarvis_connect_"):
        code = data.replace("btn_jarvis_connect_", "")
        context.args = [code]
        await connectjarvis_command(update, context)

