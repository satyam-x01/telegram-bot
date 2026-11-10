import os
import sqlite3
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DB_PATH = Path(
    os.getenv("DATABASE_PATH", str(Path(__file__).parent / "music_bot.db"))
)

class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    language TEXT DEFAULT 'en',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS premium_codes (
                    code TEXT PRIMARY KEY,
                    redeemed_by INTEGER UNIQUE,
                    redeemed_at TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS premium_users (
                    user_id INTEGER PRIMARY KEY,
                    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    code_used TEXT UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS universal_store_premium_codes (
                    code TEXT PRIMARY KEY,
                    redeemed_by TEXT,
                    redeemed_at TIMESTAMP
                )
            """)
            # Play stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS play_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    song_title TEXT,
                    category TEXT,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # AI Usage table for daily limits
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_usage (
                    user_id INTEGER,
                    usage_date DATE DEFAULT (DATE('now')),
                    count INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, usage_date)
                )
            """)
            # Developer users table for unlimited AI access
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dev_users (
                    user_id INTEGER PRIMARY KEY
                )
            """)
            # Audio file_id cache table for instant sending
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audio_cache (
                    query_key TEXT PRIMARY KEY,
                    file_id TEXT,
                    title TEXT,
                    artist TEXT,
                    duration INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Blacklisted users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blacklisted_users (
                    user_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Blacklisted chats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blacklisted_chats (
                    chat_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Authorized users table per chat
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_users (
                    chat_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (chat_id, user_id)
                )
            """)
            # Maintenance mode table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_mode (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    status INTEGER DEFAULT 0
                )
            """)
            cursor.execute("INSERT OR IGNORE INTO maintenance_mode (id, status) VALUES (1, 0)")
            # Subscriptions table for 24/7 hourly astronomy auto-posts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    chat_id INTEGER PRIMARY KEY,
                    chat_type TEXT DEFAULT 'private',
                    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Daily Couple of the Day table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_couples (
                    chat_id INTEGER,
                    couple_date DATE DEFAULT (DATE('now')),
                    user1_id INTEGER,
                    user1_name TEXT,
                    user2_id INTEGER,
                    user2_name TEXT,
                    PRIMARY KEY (chat_id, couple_date)
                )
            """)
            # Personal User Playlists table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    user_id INTEGER,
                    song_title TEXT,
                    query TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, song_title)
                )
            """)
            # Jarvis Pairing & Device Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jarvis_sessions (
                    user_id INTEGER PRIMARY KEY,
                    pair_code TEXT UNIQUE,
                    status TEXT DEFAULT 'unpaired',
                    device_name TEXT DEFAULT 'Jarvis Mobile / PC',
                    nova_active_until REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Migration check for nova_active_until
            try:
                cursor.execute("ALTER TABLE jarvis_sessions ADD COLUMN nova_active_until REAL DEFAULT 0")
            except Exception:
                pass

            # Telegram Cloud Storage & MTProto Sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_telegram_sessions (
                    user_id INTEGER PRIMARY KEY,
                    phone_number TEXT,
                    session_string TEXT,
                    is_connected INTEGER DEFAULT 0,
                    active_group_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Telegram User Cloud Groups
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_cloud_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    group_name TEXT,
                    telegram_chat_id INTEGER,
                    invite_link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()


    def get_cached_audio(self, query_key: str) -> Optional[Dict]:
        key = query_key.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT file_id, title, artist, duration FROM audio_cache WHERE query_key = ?",
                (key,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "file_id": row["file_id"],
                    "title": row["title"],
                    "artist": row["artist"],
                    "duration": row["duration"]
                }
            return None

    def save_audio_cache(self, query_key: str, file_id: str, title: str, artist: str, duration: int):
        key = query_key.strip().lower()
        if not key or not file_id:
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO audio_cache (query_key, file_id, title, artist, duration)
                VALUES (?, ?, ?, ?, ?)
            """, (key, file_id, title, artist, duration))
            conn.commit()

    def add_dev_user(self, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO dev_users (user_id) VALUES (?)", (user_id,))
            conn.commit()

    def is_dev_user(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM dev_users WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None

    def add_or_update_user(self, user_id: int, username: Optional[str], first_name: Optional[str]) -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                    (username, first_name, user_id)
                )
                conn.commit()
                return row["language"] or "en"
            else:
                cursor.execute(
                    "INSERT INTO users (user_id, username, first_name, language) VALUES (?, ?, ?, 'en')",
                    (user_id, username, first_name)
                )
                conn.commit()
                return "en"

    def set_user_language(self, user_id: int, lang_code: str):
        if lang_code not in {"en", "hi", "hinglish"}:
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, language) VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
            """, (user_id, lang_code))
            conn.commit()

    def get_user_language(self, user_id: int) -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row["language"] if row and row["language"] else "en"

    def create_premium_codes(self, count: int = 100_000) -> list[str]:
        """Create unique, unused six-digit codes and persist them before export."""
        if count < 1 or count > 900_000:
            raise ValueError("Premium code count must be between 1 and 900000")
        with self._get_connection() as conn:
            existing = {row[0] for row in conn.execute("SELECT code FROM premium_codes")}
            available = 900_000 - len(existing)
            if count > available:
                raise ValueError(f"Only {available} unused six-digit codes are available")

            codes: list[str] = []
            while len(codes) < count:
                code = str(secrets.randbelow(900_000) + 100_000)
                if code not in existing:
                    existing.add(code)
                    codes.append(code)
            conn.executemany("INSERT INTO premium_codes (code) VALUES (?)", ((code,) for code in codes))
            conn.commit()
            return codes

    def redeem_premium_code(self, user_id: int, code: str) -> bool:
        """Atomically redeem a code. A code can be claimed by exactly one user."""
        return self.redeem_premium_code_status(user_id, code) == "redeemed"

    def redeem_premium_code_status(self, user_id: int, code: str) -> str:
        """Redeem once and distinguish invalid, already-used, and already-premium states."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if cursor.execute("SELECT 1 FROM premium_users WHERE user_id = ?", (user_id,)).fetchone():
                return "already_premium"
            cursor.execute(
                "UPDATE premium_codes SET redeemed_by = ?, redeemed_at = CURRENT_TIMESTAMP "
                "WHERE code = ? AND redeemed_by IS NULL",
                (user_id, code),
            )
            if cursor.rowcount != 1:
                exists = cursor.execute(
                    "SELECT 1 FROM premium_codes WHERE code = ?", (code,)
                ).fetchone()
                return "already_used" if exists else "invalid"
            cursor.execute(
                "INSERT OR IGNORE INTO premium_users (user_id, code_used) VALUES (?, ?)",
                (user_id, code),
            )
            conn.commit()
            return "redeemed"

    def is_premium_user(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            return conn.execute("SELECT 1 FROM premium_users WHERE user_id = ?", (user_id,)).fetchone() is not None

    def premium_stats(self) -> Tuple[int, int]:
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM premium_codes").fetchone()[0]
            redeemed = conn.execute("SELECT COUNT(*) FROM premium_codes WHERE redeemed_by IS NOT NULL").fetchone()[0]
            return total, redeemed

    def get_premium_codes(self) -> list[str]:
        with self._get_connection() as conn:
            return [row[0] for row in conn.execute("SELECT code FROM premium_codes ORDER BY code")]

    def import_universal_store_codes(self, codes: List[str]) -> int:
        """Import app codes into the shared server database without resetting claims."""
        normalized = {str(code).strip().upper() for code in codes}
        normalized = {code for code in normalized if len(code) == 6 and code.isalnum()}
        if not normalized:
            return 0
        with self._get_connection() as conn:
            before = conn.total_changes
            conn.executemany(
                "INSERT OR IGNORE INTO universal_store_premium_codes (code) VALUES (?)",
                ((code,) for code in normalized),
            )
            conn.commit()
            return conn.total_changes - before

    def redeem_universal_store_code(self, code: str, install_id: str) -> str:
        """Atomically claim a Universal Store code; same install retries are idempotent."""
        code = str(code).strip().upper()
        install_id = str(install_id).strip()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT redeemed_by FROM universal_store_premium_codes WHERE code = ?",
                (code,),
            ).fetchone()
            if not row:
                return "invalid"
            if row["redeemed_by"] == install_id:
                return "success"
            if row["redeemed_by"] is not None:
                return "already_used"
            cursor = conn.execute(
                "UPDATE universal_store_premium_codes "
                "SET redeemed_by = ?, redeemed_at = CURRENT_TIMESTAMP "
                "WHERE code = ? AND redeemed_by IS NULL",
                (install_id, code),
            )
            if cursor.rowcount == 1:
                conn.commit()
                return "success"
            return "already_used"

    def get_ai_usage_today(self, user_id: int) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT count FROM ai_usage WHERE user_id = ? AND usage_date = DATE('now')",
                (user_id,)
            )
            row = cursor.fetchone()
            return row["count"] if row else 0

    def increment_ai_usage_today(self, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_usage (user_id, usage_date, count) 
                VALUES (?, DATE('now'), 1)
                ON CONFLICT(user_id, usage_date) 
                DO UPDATE SET count = count + 1
            """, (user_id,))
            conn.commit()

    def log_play(self, user_id: int, song_title: str, category: str = "general"):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO play_stats (user_id, song_title, category) VALUES (?, ?, ?)",
                (user_id, song_title, category)
            )
            conn.commit()

    def get_stats(self) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total_users FROM users")
            total_users = cursor.fetchone()["total_users"]

            cursor.execute("SELECT COUNT(*) as total_plays FROM play_stats")
            total_plays = cursor.fetchone()["total_plays"]

            cursor.execute("""
                SELECT song_title, COUNT(*) as count 
                FROM play_stats 
                GROUP BY song_title 
                ORDER BY count DESC 
                LIMIT 5
            """)
            top_songs = [{"title": row["song_title"], "count": row["count"]} for row in cursor.fetchall()]

            return {
                "total_users": total_users,
                "total_plays": total_plays,
                "top_songs": top_songs
            }

    def get_detailed_users_list(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    u.user_id, 
                    u.username, 
                    u.first_name, 
                    u.joined_at,
                    COUNT(p.id) as play_count
                FROM users u
                LEFT JOIN play_stats p ON u.user_id = p.user_id
                GROUP BY u.user_id
                ORDER BY u.joined_at DESC
            """)
            results = []
            for row in cursor.fetchall():
                results.append({
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "first_name": row["first_name"],
                    "joined_at": row["joined_at"],
                    "play_count": row["play_count"]
                })
            return results

    def get_all_user_ids(self) -> List[int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            return [row["user_id"] for row in cursor.fetchall()]

    # Blacklisted Users Methods
    def is_user_blacklisted(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM blacklisted_users WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None

    def blacklist_user(self, user_id: int, reason: str = "Violation of terms"):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO blacklisted_users (user_id, reason) VALUES (?, ?)", (user_id, reason))
            conn.commit()

    def unblacklist_user(self, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM blacklisted_users WHERE user_id = ?", (user_id,))
            conn.commit()

    def get_blacklisted_users(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, reason, added_at FROM blacklisted_users")
            return [dict(row) for row in cursor.fetchall()]

    # Blacklisted Chats Methods
    def is_chat_blacklisted(self, chat_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chat_id FROM blacklisted_chats WHERE chat_id = ?", (chat_id,))
            return cursor.fetchone() is not None

    def blacklist_chat(self, chat_id: int, reason: str = "Blacklisted chat"):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO blacklisted_chats (chat_id, reason) VALUES (?, ?)", (chat_id, reason))
            conn.commit()

    def unblacklist_chat(self, chat_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM blacklisted_chats WHERE chat_id = ?", (chat_id,))
            conn.commit()

    def get_blacklisted_chats(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chat_id, reason, added_at FROM blacklisted_chats")
            return [dict(row) for row in cursor.fetchall()]

    # Authorized Users Methods
    def is_user_authed(self, chat_id: int, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM auth_users WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            return cursor.fetchone() is not None

    def auth_user(self, chat_id: int, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO auth_users (chat_id, user_id) VALUES (?, ?)", (chat_id, user_id))
            conn.commit()

    def unauth_user(self, chat_id: int, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM auth_users WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            conn.commit()

    # Maintenance Mode Methods
    def is_maintenance_mode(self) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM maintenance_mode WHERE id = 1")
            row = cursor.fetchone()
            return bool(row["status"]) if row else False

    def set_maintenance_mode(self, status: bool):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE maintenance_mode SET status = ? WHERE id = 1", (1 if status else 0,))
            conn.commit()

    # Daily Couple Methods
    def get_couple_of_day(self, chat_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user1_id, user1_name, user2_id, user2_name FROM daily_couples WHERE chat_id = ? AND couple_date = DATE('now')",
                (chat_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def set_couple_of_day(self, chat_id: int, u1_id: int, u1_name: str, u2_id: int, u2_name: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO daily_couples (chat_id, couple_date, user1_id, user1_name, user2_id, user2_name)
                VALUES (?, DATE('now'), ?, ?, ?, ?)
            """, (chat_id, u1_id, u1_name, u2_id, u2_name))
            conn.commit()

    # User Playlist Methods
    def add_to_playlist(self, user_id: int, song_title: str, query: str = ""):
        title = song_title.strip()
        search_q = query.strip() or title
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO playlists (user_id, song_title, query)
                VALUES (?, ?, ?)
            """, (user_id, title, search_q))
            conn.commit()

    def remove_from_playlist(self, user_id: int, song_title: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM playlists WHERE user_id = ? AND song_title = ?", (user_id, song_title.strip()))
            conn.commit()

    def get_user_playlist(self, user_id: int) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT song_title, query, added_at FROM playlists WHERE user_id = ? ORDER BY added_at DESC", (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def clear_user_playlist(self, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM playlists WHERE user_id = ?", (user_id,))
            conn.commit()

    # Jarvis Session & Device Pairing Methods
    def generate_jarvis_code(self, user_id: int) -> str:
        import random
        import string
        num_code = "".join(random.choices(string.digits, k=6))
        pair_code = f"JRV-{num_code}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO jarvis_sessions (user_id, pair_code, status, updated_at)
                VALUES (?, ?, 'unpaired', CURRENT_TIMESTAMP)
            """, (user_id, pair_code))
            conn.commit()
        return pair_code

    def connect_jarvis_code(self, user_id: int, input_code: str, device_name: str = "Jarvis Mobile / PC") -> bool:
        raw_code = input_code.strip().upper()
        digits = "".join(filter(str.isdigit, raw_code))
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Direct match check
            cursor.execute("SELECT user_id, pair_code FROM jarvis_sessions WHERE user_id = ? AND (pair_code = ? OR pair_code LIKE ?)", (user_id, raw_code, f"%{digits}"))
            row = cursor.fetchone()

            # Global fallback check
            if not row and digits:
                cursor.execute("SELECT user_id, pair_code FROM jarvis_sessions WHERE pair_code LIKE ?", (f"%{digits}",))
                row = cursor.fetchone()

            if row:
                target_user_id = row["user_id"]
                cursor.execute("""
                    UPDATE jarvis_sessions 
                    SET status = 'connected', device_name = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                """, (device_name, target_user_id))
                conn.commit()
                return True
            return False

    def get_jarvis_session(self, user_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, pair_code, status, device_name, updated_at FROM jarvis_sessions WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def is_jarvis_connected(self, user_id: int) -> bool:
        session = self.get_jarvis_session(user_id)
        return bool(session and session.get("status") == "connected")

    def disconnect_jarvis(self, user_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE jarvis_sessions SET status = 'unpaired', nova_active_until = 0 WHERE user_id = ?", (user_id,))
            conn.commit()

    def start_nova_session(self, user_id: int, duration_seconds: int = 300) -> float:
        import time
        expiry_time = time.time() + duration_seconds
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jarvis_sessions 
                SET nova_active_until = ?, status = 'connected', updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (expiry_time, user_id))
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO jarvis_sessions (user_id, status, nova_active_until)
                    VALUES (?, 'connected', ?)
                """, (user_id, expiry_time))
            conn.commit()
        return expiry_time

    def is_nova_session_active(self, user_id: int) -> bool:
        import time
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nova_active_until FROM jarvis_sessions WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row["nova_active_until"]:
                return float(row["nova_active_until"]) > time.time()
            return False

    def get_nova_session_remaining(self, user_id: int) -> int:
        import time
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nova_active_until FROM jarvis_sessions WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row["nova_active_until"]:
                rem = int(float(row["nova_active_until"]) - time.time())
                return max(0, rem)
            return 0


    # Astronomy Hourly Subscription Methods
    def add_subscription(self, chat_id: int, chat_type: str = "private") -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO subscriptions (chat_id, chat_type, subscribed_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (chat_id, chat_type))
            conn.commit()
            return True

    def remove_subscription(self, chat_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM subscriptions WHERE chat_id = ?", (chat_id,))
            conn.commit()
            return True

    def is_subscribed(self, chat_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chat_id FROM subscriptions WHERE chat_id = ?", (chat_id,))
            return cursor.fetchone() is not None

    def get_all_subscriptions(self) -> List[int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chat_id FROM subscriptions")
            return [row["chat_id"] for row in cursor.fetchall()]

    # ─── Telegram Cloud Storage & MTProto Sessions ───
    def save_user_telegram_session(self, user_id: int, phone_number: str, session_string: str, is_connected: int = 1) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_telegram_sessions (user_id, phone_number, session_string, is_connected, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    phone_number = excluded.phone_number,
                    session_string = excluded.session_string,
                    is_connected = excluded.is_connected,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, phone_number, session_string, is_connected))
            conn.commit()
            return True

    def get_user_telegram_session(self, user_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, phone_number, session_string, is_connected, active_group_id, created_at, updated_at
                FROM user_telegram_sessions
                WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def delete_user_telegram_session(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_telegram_sessions WHERE user_id = ?", (user_id,))
            conn.commit()
            return True

    def set_user_active_cloud_group(self, user_id: int, group_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_telegram_sessions
                SET active_group_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (group_id, user_id))
            conn.commit()
            return True

    def get_user_active_cloud_group(self, user_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT g.id, g.user_id, g.group_name, g.telegram_chat_id, g.invite_link, g.created_at
                FROM user_telegram_sessions s
                JOIN user_cloud_groups g ON s.active_group_id = g.id
                WHERE s.user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            
            # Fallback: return the most recently created group for this user if active_group_id not set
            cursor.execute("""
                SELECT id, user_id, group_name, telegram_chat_id, invite_link, created_at
                FROM user_cloud_groups
                WHERE user_id = ?
                ORDER BY id DESC LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                self.set_user_active_cloud_group(user_id, res["id"])
                return res
            return None

    def add_cloud_group(self, user_id: int, group_name: str, telegram_chat_id: int, invite_link: str = "") -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_cloud_groups (user_id, group_name, telegram_chat_id, invite_link)
                VALUES (?, ?, ?, ?)
            """, (user_id, group_name, telegram_chat_id, invite_link))
            group_id = cursor.lastrowid
            # Automatically set this as active group
            cursor.execute("""
                UPDATE user_telegram_sessions
                SET active_group_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (group_id, user_id))
            conn.commit()
            return group_id

    def get_user_cloud_groups(self, user_id: int) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, group_name, telegram_chat_id, invite_link, created_at
                FROM user_cloud_groups
                WHERE user_id = ?
                ORDER BY id DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_cloud_group_by_id(self, group_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                    SELECT id, user_id, group_name, telegram_chat_id, invite_link, created_at
                    FROM user_cloud_groups
                    WHERE id = ? AND user_id = ?
                """, (group_id, user_id))
            else:
                cursor.execute("""
                    SELECT id, user_id, group_name, telegram_chat_id, invite_link, created_at
                    FROM user_cloud_groups
                    WHERE id = ?
                """, (group_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def delete_cloud_group(self, group_id: int, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_cloud_groups WHERE id = ? AND user_id = ?", (group_id, user_id))
            # If deleted group was active, clear or reassign active_group_id
            cursor.execute("""
                UPDATE user_telegram_sessions
                SET active_group_id = NULL
                WHERE user_id = ? AND active_group_id = ?
            """, (user_id, group_id))
            conn.commit()
            return True

db = Database()
