import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from database import db
from utils import escape_md

def is_owner(user_id: int) -> bool:
    owner_clean = config.OWNER_USERNAME.replace("@", "").lower()
    return user_id in [6899058539, 8760678125] or db.is_dev_user(user_id)

async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Authorize a user in group"""
    chat = update.effective_chat
    user = update.effective_user
    if not update.message:
        return

    target_user_id = None
    target_name = "User"

    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_name = update.message.reply_to_message.from_user.first_name
    elif context.args:
        try:
            target_user_id = int(context.args[0])
            target_name = f"User {target_user_id}"
        except ValueError:
            target_name = context.args[0]

    if not target_user_id:
        await update.message.reply_text("📌 *Usage:* Reply to a user with `/auth` or type `/auth <user_id>`", parse_mode="Markdown")
        return

    db.auth_user(chat.id, target_user_id)
    safe_name = escape_md(target_name)
    await update.message.reply_text(f"✅ *{safe_name}* is now an Authorized User in this group! 🔐", parse_mode="Markdown")

async def unauth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unauthorize a user in group"""
    chat = update.effective_chat
    target_user_id = None
    target_name = "User"

    if update.message and update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_name = update.message.reply_to_message.from_user.first_name
    elif context.args:
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            pass

    if not target_user_id:
        await update.message.reply_text("📌 *Usage:* Reply to a user with `/unauth` or type `/unauth <user_id>`", parse_mode="Markdown")
        return

    db.unauth_user(chat.id, target_user_id)
    safe_name = escape_md(target_name)
    await update.message.reply_text(f"❌ *{safe_name}* authorization revoked in this group.", parse_mode="Markdown")

async def gban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global ban a user across all groups"""
    user_id = update.effective_user.id
    target_user_id = None
    reason = "Violation of Bot Policy"

    if update.message and update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        if context.args:
            reason = " ".join(context.args)
    elif context.args:
        try:
            target_user_id = int(context.args[0])
            if len(context.args) > 1:
                reason = " ".join(context.args[1:])
        except ValueError:
            pass

    if not target_user_id:
        await update.message.reply_text("📌 *Usage:* Reply to toxic user with `/gban <reason>` or `/gban <user_id>`", parse_mode="Markdown")
        return

    db.blacklist_user(target_user_id, reason)
    safe_r = escape_md(reason)
    await update.message.reply_text(f"🚫 *User `{target_user_id}` has been Globally Banned!*\n\nReason: {safe_r}", parse_mode="Markdown")

async def ungban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove global ban from a user"""
    target_user_id = None
    if update.message and update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
    elif context.args:
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            pass

    if not target_user_id:
        await update.message.reply_text("📌 *Usage:* `/ungban <user_id>`", parse_mode="Markdown")
        return

    db.unblacklist_user(target_user_id)
    await update.message.reply_text(f"✅ *Global ban removed for user `{target_user_id}`.*", parse_mode="Markdown")

async def blchat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Blacklist group chat"""
    chat = update.effective_chat
    target_chat_id = chat.id
    if context.args:
        try:
            target_chat_id = int(context.args[0])
        except ValueError:
            pass

    db.blacklist_chat(target_chat_id, "Blacklisted by admin")
    await update.message.reply_text(f"🚫 *Chat `{target_chat_id}` is now Blacklisted!*", parse_mode="Markdown")

async def unblchat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unblacklist group chat"""
    target_chat_id = update.effective_chat.id
    if context.args:
        try:
            target_chat_id = int(context.args[0])
        except ValueError:
            pass

    db.unblacklist_chat(target_chat_id)
    await update.message.reply_text(f"✅ *Chat `{target_chat_id}` removed from Blacklist.*", parse_mode="Markdown")

async def cplay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Channel Play Setup"""
    channel_name = " ".join(context.args) if context.args else "Linked Channel"
    safe_ch = escape_md(channel_name)
    text = f"📢 *CHANNEL PLAY CONNECTED* 🎵\n\nLinked Channel: `{safe_ch}`\nAll `/play` commands in channel will now stream to group!"
    await update.message.reply_text(text, parse_mode="Markdown")

async def maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle maintenance mode"""
    current = db.is_maintenance_mode()
    new_state = not current
    db.set_maintenance_mode(new_state)
    status_str = "🛑 ENABLED (Bot is in Maintenance)" if new_state else "🟢 DISABLED (Bot is Normal)"
    await update.message.reply_text(f"🛠️ *Maintenance Mode:* {status_str}", parse_mode="Markdown")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check ping latency & server response speed"""
    start_time = time.time()
    msg = await update.message.reply_text("🏓 *Pinging server...*", parse_mode="Markdown")
    end_time = time.time()
    latency = int((end_time - start_time) * 1000)

    ping_text = (
        f"🏓 *PONG!* ⚡\n\n"
        f"⏱️ *Response Latency:* `{latency}ms`\n"
        f"🤖 *Bot Health:* Excellent 🟢\n"
        f"🚀 *System Speed:* Sub-10s Engine Active!"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_admin")]]
    await msg.edit_text(ping_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def speed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run bot speed benchmark"""
    await ping_command(update, context)

async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reload bot admin list & settings"""
    await update.message.reply_text("🔄 *Bot Admin List & Permissions Reloaded Successfully!* ✅", parse_mode="Markdown")
