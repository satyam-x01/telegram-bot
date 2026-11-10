import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("WHATSAPP_DATA_DIR", str(BASE_DIR / "data")))
DOWNLOADS_DIR = DATA_DIR / "downloads"
CONFIG_FILE = DATA_DIR / "config.json"
USERS_FILE = DATA_DIR / "users.json"
BIN_DIR = BASE_DIR / "bin"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
BIN_DIR.mkdir(parents=True, exist_ok=True)

# Add bin directory to PATH for ffmpeg
bin_str = str(BIN_DIR)
if bin_str not in os.environ.get("PATH", ""):
    os.environ["PATH"] = bin_str + os.pathsep + os.environ.get("PATH", "")

# Logging setup
LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("WhatsAppBot")

DEFAULT_CONFIG = {
    "bot_password": os.environ.get("BOT_PASSWORD", "satyam08052010"),
    "creator_name": "Satyam Developer",
    "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
    "gemini_model": "gemini-flash-latest",
    "video_retention_hours": 24,
    "port": int(os.environ.get("PORT", 5000)),
    "public_url": os.environ.get("PUBLIC_URL", "")
}

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cfg = DEFAULT_CONFIG.copy()
                    cfg.update(data)
                    return cfg
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def update(self, key_values: dict):
        self.config.update(key_values)
        self.save_config()

def get_server_url() -> str:
    """Return active Cloudflare tunnel URL, public URL if set, otherwise auto-detect LAN IP and port."""
    # 1. Check live Cloudflare tunnel
    try:
        from modules.tunnel import tunnel_manager
        if tunnel_manager.is_running and tunnel_manager.tunnel_url:
            return tunnel_manager.tunnel_url.rstrip("/")
    except Exception:
        pass

    # 2. Check saved public_url in config
    pub = config_manager.get("public_url", "").strip()
    if pub:
        return pub.rstrip("/")

    # 3. Fallback to LAN IP
    port = config_manager.get("port", 5000)
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return f"http://{ip}:{port}"
    except Exception:
        return f"http://localhost:{port}"

def jid_to_str(jid) -> str:
    """Normalize any JID object or string into standard 'user@server' format."""
    if not jid:
        return ""
    if isinstance(jid, str):
        if "User:" in jid and "Server:" in jid:
            import re
            u_m = re.search(r'User:\s*"([^"]+)"', jid)
            s_m = re.search(r'Server:\s*"([^"]+)"', jid)
            if u_m:
                u = u_m.group(1)
                s = s_m.group(1) if s_m else "lid"
                return f"{u}@{s}"
        clean = jid.strip()
        if "@" in clean:
            return clean
        if clean.isdigit():
            return f"{clean}@s.whatsapp.net"
        return clean

    user = getattr(jid, "User", "")
    server = getattr(jid, "Server", "")
    if user and server:
        return f"{user}@{server}"
    elif user:
        return f"{user}@s.whatsapp.net"
    return str(jid).strip()

def str_to_jid(jid_val):
    """Convert any string or JID object into a valid Neonize JID object."""
    from neonize.proto.Neonize_pb2 import JID
    if isinstance(jid_val, JID):
        return jid_val
    clean = jid_to_str(jid_val)
    if "@" in clean:
        user, server = clean.rsplit("@", 1)
        return JID(User=user, Server=server, Device=0, RawAgent=0, Integrator=0, IsEmpty=False)
    return JID(User=clean, Server="s.whatsapp.net", Device=0, RawAgent=0, Integrator=0, IsEmpty=False)

def create_default_slots(legacy_prompt="", legacy_interval=5, legacy_count=0, legacy_history=None):
    return {
        "1": {
            "slot": 1,
            "name": "Automation #1",
            "prompt": legacy_prompt or "",
            "interval_minutes": legacy_interval if legacy_interval else 5,
            "discovery_count": legacy_count,
            "last_run": 0,
            "history": legacy_history if legacy_history else []
        },
        "2": {
            "slot": 2,
            "name": "Automation #2",
            "prompt": "",
            "interval_minutes": 5,
            "discovery_count": 0,
            "last_run": 0,
            "history": []
        },
        "3": {
            "slot": 3,
            "name": "Automation #3",
            "prompt": "",
            "interval_minutes": 5,
            "discovery_count": 0,
            "last_run": 0,
            "history": []
        }
    }

class UserManager:
    """Manages individual user configurations, multiple automation slots (1, 2, 3), custom prompts, intervals, and history."""

    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = self.load_users()

    def load_users(self) -> Dict[str, Dict[str, Any]]:
        raw_users = {}
        if USERS_FILE.exists():
            try:
                with open(USERS_FILE, "r", encoding="utf-8") as f:
                    raw_users = json.load(f)
            except Exception as e:
                logger.error(f"Error loading users: {e}")
                raw_users = {}

        cleaned = {}
        needs_save = False
        for k, v in raw_users.items():
            clean_k = jid_to_str(k)
            if clean_k != k:
                needs_save = True
            v["jid"] = clean_k

            # Migrate or ensure 3 automation slots
            if "automations" not in v or not isinstance(v["automations"], dict):
                needs_save = True
                v["automations"] = create_default_slots(
                    legacy_prompt=v.get("custom_prompt", ""),
                    legacy_interval=v.get("interval_minutes", 5),
                    legacy_count=v.get("discovery_count", 0),
                    legacy_history=v.get("history", [])
                )
            if "selected_slot" not in v:
                v["selected_slot"] = 1
                needs_save = True

            # Ensure all 3 slots exist
            for s in ["1", "2", "3"]:
                if s not in v["automations"]:
                    v["automations"][s] = {
                        "slot": int(s),
                        "name": f"Automation #{s}",
                        "prompt": "",
                        "interval_minutes": 5,
                        "discovery_count": 0,
                        "last_run": 0,
                        "history": []
                    }
                    needs_save = True

            # User-level AI Key and query quota tracking
            if "custom_gemini_key" not in v:
                v["custom_gemini_key"] = ""
                needs_save = True
            if "ai_query_count" not in v:
                v["ai_query_count"] = 0
                needs_save = True

            # Sync active slot to top-level fields for backwards compatibility
            curr_slot = v["automations"].get(str(v.get("selected_slot", 1)), v["automations"]["1"])
            v["custom_prompt"] = curr_slot.get("prompt", "")
            v["interval_minutes"] = curr_slot.get("interval_minutes", 5)

            cleaned[clean_k] = v

        if needs_save:
            try:
                with open(USERS_FILE, "w", encoding="utf-8") as f:
                    json.dump(cleaned, f, indent=2, ensure_ascii=False)
                logger.info("Migrated legacy users.json to 3-slot automation structure.")
            except Exception as e:
                logger.error(f"Error saving migrated users: {e}")

        return cleaned

    def save_users(self):
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving users: {e}")

    def get_or_create_user(self, jid_val) -> Dict[str, Any]:
        jid = jid_to_str(jid_val)
        if jid not in self.users:
            self.users[jid] = {
                "jid": jid,
                "state": "UNAUTHENTICATED",
                "is_active": False,
                "selected_slot": 1,
                "custom_prompt": "",
                "interval_minutes": 5,
                "last_run": 0,
                "discovery_count": 0,
                "history": [],
                "automations": create_default_slots(),
                "custom_gemini_key": "",
                "ai_query_count": 0,
                "name": ""
            }
            self.save_users()
        user = self.users[jid]
        if "automations" not in user:
            user["automations"] = create_default_slots()
            user["selected_slot"] = 1
            self.save_users()
        if "custom_gemini_key" not in user:
            user["custom_gemini_key"] = ""
            self.save_users()
        if "ai_query_count" not in user:
            user["ai_query_count"] = 0
            self.save_users()
        if "name" not in user:
            user["name"] = ""
            self.save_users()
        return user

    def update_user(self, jid_val, **kwargs):
        jid = jid_to_str(jid_val)
        user = self.get_or_create_user(jid)
        user.update(kwargs)

        # If interval_minutes, custom_prompt, or last_run updated at user level, sync to selected slot
        slot_key = str(user.get("selected_slot", 1))
        if slot_key in user.get("automations", {}):
            slot = user["automations"][slot_key]
            if "interval_minutes" in kwargs:
                slot["interval_minutes"] = kwargs["interval_minutes"]
            if "custom_prompt" in kwargs:
                slot["prompt"] = kwargs["custom_prompt"]
            if "last_run" in kwargs:
                slot["last_run"] = kwargs["last_run"]

        self.save_users()
        return user

    def get_selected_automation(self, jid_val) -> tuple[int, Dict[str, Any]]:
        user = self.get_or_create_user(jid_val)
        slot_num = int(user.get("selected_slot", 1))
        slot_key = str(slot_num)
        slot_data = user.get("automations", {}).get(slot_key)
        if not slot_data:
            slot_data = {
                "slot": slot_num,
                "name": f"Automation #{slot_num}",
                "prompt": "",
                "interval_minutes": 5,
                "discovery_count": 0,
                "last_run": 0,
                "history": []
            }
            user.setdefault("automations", {})[slot_key] = slot_data
            self.save_users()
        return slot_num, slot_data

    def select_slot(self, jid_val, slot_num: int) -> tuple[bool, Dict[str, Any]]:
        """Select slot 1, 2, or 3. Active execution pauses until /start is given."""
        if slot_num not in [1, 2, 3]:
            return False, {}
        user = self.get_or_create_user(jid_val)
        user["selected_slot"] = slot_num
        user["is_active"] = False  # Keep stopped until /start is called
        slot_key = str(slot_num)
        slot_data = user.get("automations", {}).get(slot_key, {})

        # Sync top-level fields
        user["custom_prompt"] = slot_data.get("prompt", "")
        user["interval_minutes"] = slot_data.get("interval_minutes", 5)
        self.save_users()
        return True, slot_data

    def set_slot_prompt(self, jid_val, slot_num: int, prompt: str, interval: Optional[int] = None, name: str = ""):
        if slot_num not in [1, 2, 3]:
            return None
        user = self.get_or_create_user(jid_val)
        slot_key = str(slot_num)
        slot = user.setdefault("automations", {}).setdefault(slot_key, {
            "slot": slot_num,
            "name": f"Automation #{slot_num}",
            "prompt": "",
            "interval_minutes": 5,
            "discovery_count": 0,
            "last_run": 0,
            "history": []
        })
        slot["prompt"] = prompt.strip()
        if interval:
            slot["interval_minutes"] = max(1, interval)
        if name:
            slot["name"] = name
        elif not slot.get("name") or slot["name"] == f"Automation #{slot_num}":
            # Auto-title from first 25 chars
            first_line = prompt.strip().split("\n")[0][:30]
            slot["name"] = first_line or f"Automation #{slot_num}"

        if user.get("selected_slot", 1) == slot_num:
            user["custom_prompt"] = slot["prompt"]
            user["interval_minutes"] = slot.get("interval_minutes", 5)

        self.save_users()
        return slot

    def set_slot_interval(self, jid_val, interval: int, slot_num: Optional[int] = None):
        user = self.get_or_create_user(jid_val)
        target_slot = slot_num if slot_num in [1, 2, 3] else int(user.get("selected_slot", 1))
        slot_key = str(target_slot)
        if slot_key in user.get("automations", {}):
            user["automations"][slot_key]["interval_minutes"] = max(1, interval)
            if user.get("selected_slot", 1) == target_slot:
                user["interval_minutes"] = max(1, interval)
            self.save_users()
            return True
        return False

    def delete_slot(self, jid_val, slot_num: int) -> bool:
        if slot_num not in [1, 2, 3]:
            return False
        user = self.get_or_create_user(jid_val)
        slot_key = str(slot_num)
        user.setdefault("automations", {})[slot_key] = {
            "slot": slot_num,
            "name": f"Automation #{slot_num}",
            "prompt": "",
            "interval_minutes": 5,
            "discovery_count": 0,
            "last_run": 0,
            "history": []
        }
        if user.get("selected_slot", 1) == slot_num:
            user["custom_prompt"] = ""
            user["is_active"] = False
        self.save_users()
        return True

    def add_user_history(self, jid_val, item: dict, slot_num: Optional[int] = None):
        jid = jid_to_str(jid_val)
        user = self.get_or_create_user(jid)
        target_slot = slot_num if slot_num in [1, 2, 3] else int(user.get("selected_slot", 1))
        slot_key = str(target_slot)

        # Slot-level history
        slot = user.setdefault("automations", {}).setdefault(slot_key, {
            "slot": target_slot, "name": f"Automation #{target_slot}", "prompt": "",
            "interval_minutes": 5, "discovery_count": 0, "last_run": 0, "history": []
        })
        slot_history = slot.setdefault("history", [])
        slot_history.append(item)
        if len(slot_history) > 200:
            slot["history"] = slot_history[-200:]
        slot["discovery_count"] = slot.get("discovery_count", 0) + 1
        slot["last_run"] = item.get("timestamp", 0)

        # Sync top-level user history
        history = user.setdefault("history", [])
        history.append(item)
        if len(history) > 200:
            user["history"] = history[-200:]
        user["discovery_count"] = user.get("discovery_count", 0) + 1
        user["last_run"] = item.get("timestamp", 0)
        self.save_users()

    def is_user_duplicate(self, jid_val, title: str, link: str = "", slot_num: Optional[int] = None) -> bool:
        """Thoroughly check if an item, app name, repository, or link was previously sent to this user across any slot."""
        if not title and not link:
            return False

        from modules.url_sanitizer import sanitize_url
        clean_target_url = sanitize_url(link).lower() if link else ""

        # Normalize title: remove emojis, punctuation, common version numbers, and stopwords
        def get_core_tokens(t: str) -> set:
            if not t:
                return set()
            # Remove emojis and special characters
            clean_t = re.sub(r'[^\w\s]', ' ', t.lower())
            tokens = set(clean_t.split())
            stopwords = {"the", "a", "an", "and", "or", "for", "in", "of", "to", "app", "apps", "tool", "tools",
                         "official", "android", "github", "client", "free", "open", "source", "latest", "new",
                         "messenger", "web", "online", "project", "v1", "v2", "v3", "beta"}
            core = {w for w in tokens if w not in stopwords and len(w) > 2 and not w.isdigit()}
            return core

        target_tokens = get_core_tokens(title)

        jid = jid_to_str(jid_val)
        user = self.get_or_create_user(jid)

        # Collect history across ALL slots for this user to prevent any duplicate discovery
        all_histories = []
        for s_data in user.get("automations", {}).values():
            all_histories.extend(s_data.get("history", []))
        if "history" in user and isinstance(user["history"], list):
            all_histories.extend(user["history"])

        for h in all_histories:
            h_title = h.get("title", "")
            h_link = h.get("link", "")

            # 1. Exact or sanitized URL match
            if clean_target_url:
                h_clean_url = sanitize_url(h_link).lower()
                if h_clean_url and (clean_target_url == h_clean_url or clean_target_url in h_clean_url or h_clean_url in clean_target_url):
                    # Check if domain and path are identical
                    if clean_target_url.split("?")[0].rstrip("/") == h_clean_url.split("?")[0].rstrip("/"):
                        return True

            # 2. Exact or substring title match
            t_low = title.strip().lower()
            ht_low = h_title.strip().lower()
            if t_low and ht_low:
                if t_low == ht_low or t_low in ht_low or ht_low in t_low:
                    return True

            # 3. Core token overlap (e.g. 'WhatsApp Messenger' vs 'WhatsApp Beta')
            if target_tokens:
                h_tokens = get_core_tokens(h_title)
                if h_tokens:
                    # If target is a single strong brand word (e.g. 'whatsapp', 'telegram', 'blender') and it matches
                    intersection = target_tokens & h_tokens
                    if len(target_tokens) <= 2 and intersection == target_tokens:
                        return True
                    if len(intersection) >= 2 and len(intersection) >= min(len(target_tokens), len(h_tokens)) * 0.7:
                        return True

        return False

    def get_all_active_users(self) -> list:
        active = []
        for u in self.users.values():
            if not u.get("is_active"):
                continue
            sel_slot = str(u.get("selected_slot", 1))
            slot_data = u.get("automations", {}).get(sel_slot, {})
            if slot_data.get("prompt") and slot_data.get("interval_minutes"):
                active.append(u)
        return active

    def set_user_api_key(self, jid_val, api_key: str):
        """Set user's personal Gemini API key for unlimited AI usage."""
        jid = jid_to_str(jid_val)
        user = self.get_or_create_user(jid)
        user["custom_gemini_key"] = api_key.strip()
        self.save_users()
        logger.info(f"Custom Gemini API key saved for user {jid}")

    def remove_user_api_key(self, jid_val):
        """Remove user's personal Gemini API key and return to default quota."""
        jid = jid_to_str(jid_val)
        user = self.get_or_create_user(jid)
        user["custom_gemini_key"] = ""
        self.save_users()
        logger.info(f"Custom Gemini API key removed for user {jid}")

    def get_user_api_key(self, jid_val) -> Optional[str]:
        """Get user's personal Gemini API key if set."""
        jid = jid_to_str(jid_val)
        user = self.get_or_create_user(jid)
        key = user.get("custom_gemini_key", "").strip()
        return key if key else None

    def increment_ai_query_count(self, jid_val) -> int:
        """Increment count of questions asked using default host API key."""
        jid = jid_to_str(jid_val)
        user = self.get_or_create_user(jid)
        user["ai_query_count"] = user.get("ai_query_count", 0) + 1
        self.save_users()
        return user["ai_query_count"]

    def reset_ai_query_count(self, jid_val):
        """Reset the user's AI query count to 0."""
        jid = jid_to_str(jid_val)
        user = self.get_or_create_user(jid)
        user["ai_query_count"] = 0
        self.save_users()


config_manager = ConfigManager()
user_manager = UserManager()
