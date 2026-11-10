import os

def escape_md(text: str) -> str:
    """Escape special characters for Telegram Markdown v1."""
    if not text:
        return ""
    s = str(text)
    # Characters that break Telegram Markdown v1 parsing
    for char in ['*', '_', '`', '[']:
        s = s.replace(char, f'\\{char}')
    return s

def purge_all_downloads():
    """Purge all temporary downloaded songs and videos from PC disk."""
    try:
        from config import DOWNLOAD_DIR, BASE_DIR
        import shutil

        # 1. Clean downloads directory
        if os.path.exists(DOWNLOAD_DIR):
            for item in os.listdir(DOWNLOAD_DIR):
                item_path = os.path.join(DOWNLOAD_DIR, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"Error purging file {item_path}: {e}")

        # 2. Clean leftover media files in BASE_DIR
        media_extensions = ('.mp4', '.m4a', '.mp3', '.webm', '.part', '.mkv', '.mov', '.avi', '.zip')
        for item in os.listdir(BASE_DIR):
            if item.endswith(media_extensions):
                item_path = os.path.join(BASE_DIR, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                except Exception as e:
                    print(f"Error purging base media file {item_path}: {e}")
    except Exception as e:
        print(f"Error in purge_all_downloads: {e}")

async def check_group_admin_permission(update, context) -> bool:
    """Check if the user is authorized to control the bot in group chats.
    In private chats (DM): Always allowed (True).
    In group/supergroup: Allowed ONLY if user is a Group Administrator, Bot Owner, or Authorized User.
    """
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return True

    # Private chats (Direct Messages): Everyone can control the bot
    if chat.type == "private":
        return True

    # Check Bot Owner / Dev users bypass
    from database import db
    if user.id in [6899058539, 8760678125] or db.is_dev_user(user.id) or db.is_user_authed(chat.id, user.id):
        return True

    # In Group / Supergroup: Check if user is a Telegram Group Administrator or Creator
    try:
        member = await context.bot.get_chat_member(chat_id=chat.id, user_id=user.id)
        if member.status in ["creator", "administrator"]:
            return True
    except Exception as e:
        print(f"Notice: Could not fetch chat member status in group {chat.id}: {e}")

    # Not authorized - Send restriction alert
    msg_text = "⚠️ *GROUP RESTRICTION ALERT!* 🛡️\n\nOnly *Group Administrators* can use and control this bot in group chats!"
    if update.message:
        try:
            await update.message.reply_text(msg_text, parse_mode="Markdown")
        except Exception:
            pass
    elif update.callback_query:
        try:
            await update.callback_query.answer("⚠️ Only Group Admins can control this bot in groups!", show_alert=True)
        except Exception:
            pass

    return False


