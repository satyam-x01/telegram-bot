import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

import json

# Load credentials from .bot_credentials.json (saved by Host App) or .env
cred_path = Path(__file__).parent / ".bot_credentials.json"
saved_creds = {}
if cred_path.exists():
    try:
        with open(cred_path, "r", encoding="utf-8") as f:
            saved_creds = json.load(f)
    except Exception:
        pass

# Bot Credentials
# Let the explicit .env token override stale host-app credentials.
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or saved_creds.get("bot_token", "").strip()
GEMINI_API_KEY = saved_creds.get("gemini_api_key") or os.getenv("GEMINI_API_KEY", "").strip()
NASA_API_KEY = saved_creds.get("nasa_api_key") or os.getenv("NASA_API_KEY", "80hAffCZFhiKukatz44X4iJ15mkdQvgfut50qWGd").strip()

# Telegram MTProto API Credentials (for Cloud Storage & User Group Creation)
raw_api_id = saved_creds.get("api_id") or os.getenv("TELEGRAM_API_ID", "2040").strip()
try:
    TELEGRAM_API_ID = int(raw_api_id) if raw_api_id else 2040
except ValueError:
    TELEGRAM_API_ID = 2040
TELEGRAM_API_HASH = saved_creds.get("api_hash") or os.getenv("TELEGRAM_API_HASH", "b18441a1ac60e7031d112efc4646b16e").strip()

# Owner & Bot Username Configuration
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "@s2u_007").strip()
if not OWNER_USERNAME.startswith("@"):
    OWNER_USERNAME = f"@{OWNER_USERNAME}"

BOT_USERNAME = ""

# Application Settings
DEFAULT_LANG = os.getenv("DEFAULT_LANGUAGE", "en").lower().strip()
BASE_DIR = Path(__file__).parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Supported Languages
SUPPORTED_LANGUAGES = {
    "en": "🇬🇧 English",
    "hi": "🇮🇳 हिन्दी (Hindi)",
    "hinglish": "🇮🇳 Hinglish"
}

# Song Categories across all languages
GENRES = {
    "phonk": ["Drift Phonk", "Brazilian Phonk", "Aggressive Phonk", "Chill Phonk", "Slowed + Reverb Phonk"],
    "beats": ["Lo-Fi Beats", "Hip-Hop Beats", "Trap Beats", "Cyberpunk Beats", "Chillhop"],
    "all_language_music": ["Hindi Hits", "Punjabi Pop", "English Billboard Top", "Haryanvi Beats", "Bhojpuri Hits", "South Indian Beats", "K-Pop", "Global Viral Hits"]
}
