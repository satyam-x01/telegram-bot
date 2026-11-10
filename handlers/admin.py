from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from database import db
from locales import get_text
from utils import escape_md

def is_owner(username: str, user_id: int) -> bool:
    if not username:
        return False
    clean_config_owner = config.OWNER_USERNAME.replace("@", "").lower()
    clean_user = username.replace("@", "").lower()
    return clean_user == clean_config_owner

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = db.get_user_language(user.id)
    safe_owner = escape_md(config.OWNER_USERNAME)

    if not is_owner(user.username, user.id):
        unauth_msg = get_text(lang, "unauthorized", owner=safe_owner)
        await update.message.reply_text(unauth_msg, parse_mode="Markdown")
        return

    stats = db.get_stats()
    text = get_text(
        lang, "admin_dashboard",
        total_users=stats["total_users"],
        total_plays=stats["total_plays"]
    )

    keyboard = [
        [InlineKeyboardButton("📊 Refresh Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast Instructions", callback_data="admin_broadcast_help")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ]

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = db.get_user_language(user.id)
    safe_owner = escape_md(config.OWNER_USERNAME)

    if not is_owner(user.username, user.id):
        await update.message.reply_text(get_text(lang, "unauthorized", owner=safe_owner), parse_mode="Markdown")
        return

    stats = db.get_stats()
    top_list = "\n".join([f"• `{escape_md(s['title'])}` ({s['count']} plays)" for s in stats["top_songs"]]) or "None yet"

    msg = (
        f"📊 *Bot Detailed Analytics* 📈\n\n"
        f"👥 *Total Registered Users:* `{stats['total_users']}`\n"
        f"🎶 *Total Song Plays:* `{stats['total_plays']}`\n\n"
        f"🔥 *Top Songs Played:*\n{top_list}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

DEV_PASSWORD = "satyam@08052010"

async def dev_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not context.args:
        prompt_msg = (
            "🔐 *Developer Mode Access*\n\n"
            "Please enter the developer password to unlock user inspection & **Unlimited AI Tune Finder** privileges:\n\n"
            "👉 *Usage:* `/dev <password>`"
        )
        await update.message.reply_text(prompt_msg, parse_mode="Markdown")
        return

    provided_password = context.args[0].strip()
    if provided_password != DEV_PASSWORD:
        await update.message.reply_text(
            "🔒 *Developer Access Restricted*\n\n"
            "❌ *Access Denied:* Incorrect developer password.\n"
            "👉 *Usage:* `/dev <password>`",
            parse_mode="Markdown"
        )
        return

    # Authenticate developer for unlimited AI tune searches
    db.add_dev_user(user.id)

    users_list = db.get_detailed_users_list()
    total_users = len(users_list)
    
    user_entries = []
    for idx, u in enumerate(users_list, 1):
        uname = f"@{escape_md(u['username'])}" if u['username'] else "No Username"
        fname = escape_md(u['first_name'] or 'User')
        uid = u['user_id']
        plays = u['play_count']
        user_entries.append(f"{idx}. 👤 *{fname}* ({uname})\n   🆔 ID: `{uid}` | 🎶 Plays: `{plays}`")

    users_formatted = "\n\n".join(user_entries) if user_entries else "No users registered yet."

    header = (
        f"👑 *Developer Inspection Panel* 🔐\n"
        f"⚡ *Developer Status:* Verified (Unlimited AI Access Activated!)\n\n"
        f"👥 *Total Registered Users:* `{total_users}`\n"
        f"────────────────────────\n\n"
        f"{users_formatted}"
    )

    await update.message.reply_text(header, parse_mode="Markdown")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = db.get_user_language(user.id)
    safe_owner = escape_md(config.OWNER_USERNAME)

    if not is_owner(user.username, user.id):
        await update.message.reply_text(get_text(lang, "unauthorized", owner=safe_owner), parse_mode="Markdown")
        return

    if not context.args:
        await update.message.reply_text(
            "📢 *Usage:* `/broadcast <message to send to all users>`\n\n"
            "Example:\n`/broadcast 🎵 New Phonk and Hindi songs added to bot!`",
            parse_mode="Markdown"
        )
        return

    raw_broadcast = " ".join(context.args)
    safe_broadcast = escape_md(raw_broadcast)
    user_ids = db.get_all_user_ids()

    status_msg = await update.message.reply_text(get_text(lang, "broadcast_started", count=len(user_ids)), parse_mode="Markdown")

    success = 0
    failed = 0
    for u_id in user_ids:
        try:
            await context.bot.send_message(chat_id=u_id, text=f"📢 *Announcement from Owner ({safe_owner}):*\n\n{safe_broadcast}", parse_mode="Markdown")
            success += 1
        except Exception:
            failed += 1

    complete_text = get_text(lang, "broadcast_complete", success=success, failed=failed)
    await status_msg.edit_text(complete_text, parse_mode="Markdown")
