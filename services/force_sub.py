import logging
from typing import List, Dict, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from database import db

logger = logging.getLogger(__name__)

# Official Required Channels / Groups
REQUIRED_CHANNELS = [
    {
        "id": "cosmic_jarvis",
        "name": "👥 Cosmic Jarvis Group",
        "username": "@cosmic_jarvis",
        "url": "https://t.me/cosmic_jarvis"
    },
    {
        "id": "cosmic_setion",
        "name": "📢 Cosmic Section Channel",
        "username": "@cosmic_setion",
        "url": "https://t.me/cosmic_setion"
    }
]

def is_exempt_user(user_id: int, username: str = "") -> bool:
    """Bot owner and developer users bypass the force subscribe check."""
    owner_clean = config.OWNER_USERNAME.replace("@", "").lower().strip()
    if username and username.lower().replace("@", "").strip() == owner_clean:
        return True
    return user_id in [6899058539, 8760678125] or db.is_dev_user(user_id)

async def check_user_joined_all(bot, user_id: int, username: str = "") -> Tuple[bool, List[Dict]]:
    """Checks whether the user has joined all required channels/groups."""
    if is_exempt_user(user_id, username):
        return True, []

    missing = []
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch["username"], user_id=user_id)
            if member.status not in ["creator", "administrator", "member", "restricted"]:
                missing.append(ch)
        except Exception as e:
            err_text = str(e).lower()
            # If user has not joined
            if "participant_id_invalid" in err_text or "user not found" in err_text:
                missing.append(ch)
            elif "member list is inaccessible" in err_text or "chat_admin_required" in err_text:
                logger.warning(f"Bot is not Admin in {ch['username']} to check members: {e}")
                missing.append(ch)
            else:
                logger.error(f"Error checking membership for {ch['username']}: {e}")
                missing.append(ch)

    return len(missing) == 0, missing

def get_force_sub_keyboard() -> InlineKeyboardMarkup:
    """Returns inline buttons for joining required channels and verifying."""
    keyboard = []
    for ch in REQUIRED_CHANNELS:
        keyboard.append([InlineKeyboardButton(f"👉 Join {ch['name']}", url=ch["url"])])
    keyboard.append([InlineKeyboardButton("🔄 Verify / I Have Joined ✅", callback_data="check_fsub")])
    return InlineKeyboardMarkup(keyboard)

def get_force_sub_text(user_first_name: str, missing_channels: List[Dict] = None) -> str:
    """Returns a locked screen message prompting the user to join channels."""
    channels_display = ""
    for idx, ch in enumerate(REQUIRED_CHANNELS, 1):
        channels_display += f"{idx}️⃣ [{ch['name']}]({ch['url']})\n"

    return (
        f"🔒 *Access Locked! / एक्सेस लॉक है!* 🔒\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Namaste *{user_first_name}*! Bot ke sabhi features (Music 🎵, Cloud Storage ☁️, Downloader 📥, Games 🎮, AI 🤖) "
        f"unlock karne ke liye aapko pehle hamare official Channel aur Group ko join karna hoga:\n\n"
        f"{channels_display}\n"
        f"📌 *Steps:*\n"
        f"1. Upar diye gaye dono buttons par click karke Join karein.\n"
        f"2. Dono join karne ke baad niche **'🔄 Verify / I Have Joined ✅'** button par tap karein!\n\n"
        f"⚡ _Dono join karte hi bot turant unlock ho jayega!_"
    )
