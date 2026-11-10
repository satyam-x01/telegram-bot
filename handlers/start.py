import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
import config
from database import db
from locales import get_text
from utils import escape_md


MAIN_MENU_LABELS = {
    "en": {
        "cloud": "☁️ Telegram Group (Cloud Storage)", "study": "📚 24/7 Study Mode (JEE, NEET, Boards)",
        "latest": "✨ Latest Space Photo", "apod": "🌌 Today's APOD", "planet": "🪐 New Exoplanets",
        "jwst": "🔭 James Webb (JWST)", "facts": "💡 Fun Facts", "asteroids": "☄️ Near-Earth Asteroids",
        "mars": "🔴 Mars Rover View", "subscribe": "🔔 Subscribe 24/7 Hourly", "search": "🔍 AI Space & Code Search",
        "music": "🎵 Music Hub", "downloader": "📥 Downloader", "games": "🎮 Games Hub",
        "jarvis": "🤖 Jarvis Remote", "fun": "💥 Fun & Roasts",
        "welcome": "👇 Tap any button below to begin."
    },
    "hi": {
        "cloud": "☁️ टेलीग्राम ग्रुप (क्लाउड स्टोरेज)", "study": "📚 24/7 स्टडी मोड (JEE, NEET, बोर्ड)",
        "latest": "✨ नई अंतरिक्ष फोटो", "apod": "🌌 आज की APOD", "planet": "🪐 नए एक्सोप्लैनेट",
        "jwst": "🔭 जेम्स वेब (JWST)", "facts": "💡 रोचक तथ्य", "asteroids": "☄️ पृथ्वी के पास क्षुद्रग्रह",
        "mars": "🔴 मार्स रोवर व्यू", "subscribe": "🔔 24/7 अपडेट सब्सक्राइब", "search": "🔍 AI स्पेस और कोड सर्च",
        "music": "🎵 म्यूजिक हब", "downloader": "📥 डाउनलोडर", "games": "🎮 गेम्स हब",
        "jarvis": "🤖 जार्विस रिमोट", "fun": "💥 फन और रोस्ट्स",
        "welcome": "👇 शुरू करने के लिए नीचे किसी भी बटन को टैप करें।"
    },
    "hinglish": {
        "cloud": "☁️ Telegram Group (Cloud Storage)", "study": "📚 24/7 Study Mode (JEE, NEET, Boards)",
        "latest": "✨ Latest Space Photo", "apod": "🌌 Aaj ka APOD", "planet": "🪐 New Exoplanets",
        "jwst": "🔭 James Webb (JWST)", "facts": "💡 Fun Facts", "asteroids": "☄️ Near-Earth Asteroids",
        "mars": "🔴 Mars Rover View", "subscribe": "🔔 24/7 Updates Subscribe", "search": "🔍 AI Space & Code Search",
        "music": "🎵 Music Hub", "downloader": "📥 Downloader", "games": "🎮 Games Hub",
        "jarvis": "🤖 Jarvis Remote", "fun": "💥 Fun & Roasts",
        "welcome": "👇 Start karne ke liye niche kisi bhi button ko tap karein."
    },
}

async def get_bot_username(context: ContextTypes.DEFAULT_TYPE) -> str:
    if getattr(config, "BOT_USERNAME", ""):
        return config.BOT_USERNAME
    if context.bot.username:
        config.BOT_USERNAME = context.bot.username
        return context.bot.username
    try:
        me = await context.bot.get_me()
        config.BOT_USERNAME = me.username
        return me.username or "MusicBot"
    except Exception:
        return "MusicBot"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = db.add_or_update_user(user.id, user.username, user.first_name)
    labels = MAIN_MENU_LABELS.get(lang, MAIN_MENU_LABELS["en"])
    premium_badge = "💎 *SHIBH PREMIUM ACTIVE*\n\n" if db.is_premium_user(user.id) else ""
    safe_owner = escape_md(config.OWNER_USERNAME)
    bot_username = await get_bot_username(context)

    # Force Subscribe Check in Private Chats (Must Join @cosmic_jarvis & @cosmic_setion)
    if update.effective_chat and update.effective_chat.type == "private":
        from services.force_sub import check_user_joined_all, get_force_sub_keyboard, get_force_sub_text
        is_joined, missing = await check_user_joined_all(context.bot, user.id, user.username)
        if not is_joined:
            lock_text = get_force_sub_text(user.first_name, missing)
            lock_kb = get_force_sub_keyboard()
            if update.message:
                await update.message.reply_text(lock_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=lock_kb)
            elif update.callback_query:
                try:
                    await update.callback_query.edit_message_text(lock_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=lock_kb)
                except Exception:
                    await update.callback_query.message.reply_text(lock_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=lock_kb)
            return

    share_text = get_text(lang, "share_text")
    encoded_share = urllib.parse.quote(share_text)
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}&text={encoded_share}"
    add_group_url = f"https://t.me/{bot_username}?startgroup=true"

    # Interface Language Selector Row (Prompt user for language choice first)
    lang_row = []
    for code, name in config.SUPPORTED_LANGUAGES.items():
        prefix = "✅ " if code == lang else ""
        lang_row.append(InlineKeyboardButton(f"{prefix}{name}", callback_data=f"setlang_{code}"))
    
    # Screenshot-style main menu.  Each button routes to an implemented handler.
    inline_keyboard = [
        lang_row,
        [
            InlineKeyboardButton(labels["cloud"], callback_data="cs_menu")
        ],
        [
            InlineKeyboardButton(labels["study"], callback_data="st_m")
        ],
        [
            InlineKeyboardButton(labels["latest"], callback_data="astro_latest"),
            InlineKeyboardButton(labels["apod"], callback_data="astro_apod")
        ],
        [
            InlineKeyboardButton(labels["planet"], callback_data="astro_planet"),
            InlineKeyboardButton(labels["jwst"], callback_data="astro_jwst")
        ],
        [
            InlineKeyboardButton(labels["facts"], callback_data="astro_fact"),
            InlineKeyboardButton(labels["asteroids"], callback_data="astro_asteroids")
        ],
        [
            InlineKeyboardButton(labels["mars"], callback_data="astro_mars"),
            InlineKeyboardButton(labels["subscribe"], callback_data="astro_sub")
        ],
        [
            InlineKeyboardButton(labels["search"], switch_inline_query_current_chat="/search ")
        ],
        [
            InlineKeyboardButton("🔎 20-in-1 Super Search Hub", callback_data="search_hub")
        ],
        [
            InlineKeyboardButton(labels["music"], callback_data="menu_music"),
            InlineKeyboardButton(labels["downloader"], callback_data="menu_downloader")
        ],
        [
            InlineKeyboardButton("📲 WhatsApp Automation", callback_data="wa_entry")
        ],
        [
            InlineKeyboardButton(labels["games"], callback_data="menu_games"),
            InlineKeyboardButton(labels["jarvis"], callback_data="btn_jarvis_main")
        ],
        [
            InlineKeyboardButton(labels["fun"], callback_data="menu_extra"),
            InlineKeyboardButton(get_text(lang, "btn_ai"), callback_data="menu_ai")
        ],
        [
            InlineKeyboardButton("💎 SHIBH PREMIUM — ₹50", callback_data="premium_menu")
        ],
        [
            InlineKeyboardButton(get_text(lang, "btn_add_group"), url=add_group_url),
            InlineKeyboardButton(get_text(lang, "btn_share_bot"), url=share_url)
        ],
        [
            InlineKeyboardButton(get_text(lang, "btn_lang"), callback_data="menu_lang"),
            InlineKeyboardButton(get_text(lang, "btn_help"), callback_data="menu_help"),
            InlineKeyboardButton(get_text(lang, "btn_owner"), callback_data="menu_owner")
        ]
    ]

    # Persistent Bottom Reply Keyboard (All buttons active & working)
    reply_keyboard = [
        [KeyboardButton("☁️ Telegram Group"), KeyboardButton("📚 Study Mode")],
        [KeyboardButton("✨ New Space Photos"), KeyboardButton("📷 APOD Photo")],
        [KeyboardButton("🪐 New Planets"), KeyboardButton("💡 Space FunFact")],
        [KeyboardButton("☄️ Asteroids"), KeyboardButton("🔴 Mars View")],
        [KeyboardButton("🎵 Music Hub"), KeyboardButton("📥 Downloader")],
        [KeyboardButton("🎮 Games Hub"), KeyboardButton("🤖 AI Tune Finder")],
        [KeyboardButton("🌐 Language"), KeyboardButton("📜 Help"), KeyboardButton("👑 Owner")]
    ]
    reply_markup_bottom = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    welcome_msg = (
        f"{premium_badge}🚀 *Welcome to Ultimate Multi-Feature Telegram Bot!* 🌟\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Namaste *{user.first_name}*! Aapka swagat hai all-in-one assistant me! Yahan aapko milte hain:\n\n"
        f"🎵 *Music Player:* 320kbps audio, Phonk 🔥, Beats 🎧 (`/play`, `/pp`, `/pb`)\n"
        f"☁️ *Cloud Storage:* Private Telegram groups & vaults (`/storage`)\n"
        f"📥 *Media Downloader:* YouTube 1080p, IG Reels, Pinterest, GitHub (`/download`)\n"
        f"🎮 *Games Hub:* Ludo, Dice, Dart, Football, Slot (`/dice`, `/ludo`)\n"
        f"🤖 *Jarvis Remote:* Control phone & PC remotely (`/jarvis`)\n"
        f"📚 *Study Hub:* JEE, NEET, Class 10/12 notes & solutions (`/study`)\n"
        f"🌌 *Astronomy & NASA:* Deep-space photos, James Webb & Mars Rover (`/latest`, `/apod`)\n\n"
        f"_{labels['welcome']}_"
    )
    if update.message:
        await update.message.reply_text(
            welcome_msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )
        # Attach persistent bottom ReplyKeyboard menu
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="👇 *Tap a button below or type `/search <question>` to start!*",
            parse_mode="Markdown",
            reply_markup=reply_markup_bottom
        )
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                welcome_msg,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard)
            )
        except Exception:
            await update.callback_query.message.reply_text(
                welcome_msg,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard)
            )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    safe_owner = escape_md(config.OWNER_USERNAME)

    # Determine page number (1 to 6)
    page = 1
    if update.callback_query and update.callback_query.data:
        data = update.callback_query.data
        if data.startswith("help_page_"):
            try:
                page = int(data.replace("help_page_", ""))
            except ValueError:
                page = 1

    total_pages = 6
    prev_page = 6 if page == 1 else page - 1
    next_page = 1 if page == 6 else page + 1

    nav_row = [
        InlineKeyboardButton("◀️ Prev", callback_data=f"help_page_{prev_page}"),
        InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="ignore"),
        InlineKeyboardButton("Next ▶️", callback_data=f"help_page_{next_page}")
    ]
    main_menu_row = [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]

    if page == 1:
        help_text = (
            f"📜 *MASTER HELP GUIDE (1/6): 🎵 MUSIC PLAYER* 🎧\n\n"
            f"Control high-quality audio streaming & song downloads:\n\n"
            f"• `/play <song>` or `/psname <song>` : Play audio stream\n"
            f"• `/vplay <video>` : Play video music stream\n"
            f"• `/pp` or `/phonk` : Instant high-energy Phonk music 🔥\n"
            f"• `/pb` or `/beats` : Instant relaxing Beats & Lo-Fi 🎧\n"
            f"• `/ai <description>` : AI Tune & Hum finder 🤖\n"
            f"• `/song <name>` : Download MP3 track file\n"
            f"• `/playlist` : View your saved personal playlist\n"
            f"• `/queue`, `/loop`, `/shuffle`, `/seek <timestamp>`\n\n"
            f"👑 *Bot Owner:* {safe_owner}"
        )
        keyboard = [
            [
                InlineKeyboardButton("🎵 /play", callback_data="help_play"),
                InlineKeyboardButton("📹 /vplay", callback_data="help_vplay"),
                InlineKeyboardButton("🔥 /phonk", callback_data="play_phonk")
            ],
            [
                InlineKeyboardButton("🎧 /beats", callback_data="play_beats"),
                InlineKeyboardButton("🤖 /ai", callback_data="menu_ai"),
                InlineKeyboardButton("📥 /song", callback_data="btn_song_info")
            ],
            [
                InlineKeyboardButton("📜 /playlist", callback_data="btn_view_playlist"),
                InlineKeyboardButton("🎶 /queue", callback_data="help_queue"),
                InlineKeyboardButton("🔁 /loop", callback_data="help_loop"),
                InlineKeyboardButton("🔀 /shuffle", callback_data="btn_shuffle_info")
            ],
            nav_row,
            main_menu_row
        ]

    elif page == 2:
        help_text = (
            f"📜 *MASTER HELP GUIDE (2/6): 📥 MEDIA & DOWNLOADER* ⚡\n\n"
            f"Download videos, music & repositories from any social link:\n\n"
            f"• `/download <url>` or `/dl` : Universal link downloader\n"
            f"• `/yt <url>` : YouTube 1080p, 720p, 480p, 360p & MP3\n"
            f"• `/insta <url>` : Instagram Reels, IGTV & Photos\n"
            f"• `/pin <url>` : Pinterest Videos, Photos & Music\n"
            f"• `/github <url>` : GitHub Repository ZIP, Releases & Files\n"
            f"• `/gdrive <url>` : Google Drive Files, Audio & Videos\n\n"
            f"👑 *Bot Owner:* {safe_owner}"
        )
        keyboard = [
            [
                InlineKeyboardButton("🔗 /download", callback_data="btn_dl_yt_info"),
                InlineKeyboardButton("🎬 /yt (YouTube)", callback_data="btn_dl_yt_info")
            ],
            [
                InlineKeyboardButton("📸 /insta", callback_data="btn_dl_insta_info"),
                InlineKeyboardButton("📌 /pin (Pinterest)", callback_data="btn_dl_pin_info")
            ],
            [
                InlineKeyboardButton("📦 /github", callback_data="btn_dl_github_info"),
                InlineKeyboardButton("📁 /gdrive", callback_data="btn_dl_gdrive_info")
            ],
            nav_row,
            main_menu_row
        ]

    elif page == 3:
        help_text = (
            f"📜 *MASTER HELP GUIDE (3/6): 🎮 INTERACTIVE GAMES* 🎯\n\n"
            f"Play Telegram native games & fun group challenges:\n\n"
            f"• `/dice` 🎲 | `/ludo` 🎲 | `/dart` 🎯 | `/basket` 🏀\n"
            f"• `/football` ⚽ | `/slot` 🎰 | `/bowling` 🎳\n"
            f"• `/couple` ❤️ | `/love` 💘\n\n"
            f"👑 *Bot Owner:* {safe_owner}"
        )
        keyboard = [
            [
                InlineKeyboardButton("🎲 /dice", callback_data="btn_game_dice"),
                InlineKeyboardButton("🎲 /ludo", callback_data="btn_game_ludo"),
                InlineKeyboardButton("🎯 /dart", callback_data="btn_game_dart")
            ],
            [
                InlineKeyboardButton("🏀 /basket", callback_data="btn_game_basket"),
                InlineKeyboardButton("⚽ /football", callback_data="btn_game_football"),
                InlineKeyboardButton("🎰 /slot", callback_data="btn_game_slot")
            ],
            [
                InlineKeyboardButton("🎳 /bowling", callback_data="btn_game_bowling"),
                InlineKeyboardButton("❤️ /couple", callback_data="btn_game_couple"),
                InlineKeyboardButton("💘 /love", callback_data="btn_game_love")
            ],
            nav_row,
            main_menu_row
        ]

    elif page == 4:
        help_text = (
            f"📜 *MASTER HELP GUIDE (4/6): 🤖 JARVIS REMOTE AGENT* ⚡\n\n"
            f"Remotely control your Mobile & PC directly from Telegram:\n\n"
            f"• `/jarvis` : Get your unique 6-digit pair code & APK/EXE links\n"
            f"• `/connectjarvis <code>` : Connect your Mobile/PC device\n"
            f"• `/jarvisapk` | `/jarvisexe` | `/jarvishelp` (100+ Offline Commands)\n\n"
            f"👑 *Bot Owner:* {safe_owner}"
        )
        keyboard = [
            [
                InlineKeyboardButton("🤖 /jarvis Hub", callback_data="btn_jarvis_main"),
                InlineKeyboardButton("📱 /jarvisapk (APK)", callback_data="btn_jarvis_apk")
            ],
            [
                InlineKeyboardButton("💻 /jarvisexe (EXE)", callback_data="btn_jarvis_exe"),
                InlineKeyboardButton("📜 100+ Commands", callback_data="btn_jarvis_help")
            ],
            nav_row,
            main_menu_row
        ]

    elif page == 5:
        help_text = (
            f"📜 *MASTER HELP GUIDE (5/6): 💥 FUN & EXTRA UTILITIES* 🌟\n\n"
            f"Roast friends, mention group members & manage group utilities:\n\n"
            f"• `/gali <@user>` | `/galigif <@user>` | `/multigali <count>`\n"
            f"• `/wish <text>` | `/tagall <msg>` | `/welcome` | `/vclogs`\n\n"
            f"👑 *Bot Owner:* {safe_owner}"
        )
        keyboard = [
            [
                InlineKeyboardButton("💥 /gali", callback_data="btn_gali"),
                InlineKeyboardButton("🎬 /galigif", callback_data="btn_galigif"),
                InlineKeyboardButton("🏷️ /tagall", callback_data="btn_tags_info")
            ],
            [
                InlineKeyboardButton("✨ /wish", callback_data="btn_wish"),
                InlineKeyboardButton("👋 /welcome", callback_data="btn_welcome"),
                InlineKeyboardButton("🎙️ /vclogs", callback_data="btn_vclogs")
            ],
            nav_row,
            main_menu_row
        ]

    elif page == 6:
        help_text = (
            f"📜 *MASTER HELP GUIDE (6/6): ⚡ ADMIN & GOVERNANCE* 👑\n\n"
            f"Group authorization, global bans, blacklists & system controls:\n\n"
            f"• `/auth`, `/unauth`, `/gban`, `/ungban`, `/blchat`, `/cplay`, `/maintenance`, `/ping`, `/speed`, `/reload`\n\n"
            f"👑 *Bot Owner:* {safe_owner}"
        )
        keyboard = [
            [
                InlineKeyboardButton("🔐 /auth", callback_data="btn_auth_info"),
                InlineKeyboardButton("🔨 /gban", callback_data="btn_gban_info"),
                InlineKeyboardButton("🛑 /blchat", callback_data="btn_blchat_info")
            ],
            [
                InlineKeyboardButton("📻 /cplay", callback_data="btn_cplay_info"),
                InlineKeyboardButton("🛠️ /maint", callback_data="btn_maint_info"),
                InlineKeyboardButton("🏓 /ping", callback_data="btn_ping_info")
            ],
            [
                InlineKeyboardButton("⚡ /speed", callback_data="btn_ping_info"),
                InlineKeyboardButton("🔄 /reload", callback_data="help_reload")
            ],
            nav_row,
            main_menu_row
        ]

    if update.message:
        await update.message.reply_text(help_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await update.callback_query.message.reply_text(help_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def add_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    bot_username = await get_bot_username(context)

    add_group_url = f"https://t.me/{bot_username}?startgroup=true"
    text = (
        f"👥 *ADD ULTIMATE MUSIC & JARVIS BOT TO TELEGRAM GROUP* 🚀\n\n"
        f"Transform your group chat with 6 powerful feature suites:\n\n"
        f"🎵 *1. Music & Audio Streaming:* Play 100K+ songs, Phonk 🔥, Beats 🎧 & AI Tune Finder 🤖\n"
        f"📥 *2. Universal Media Downloader:* YouTube 1080p, IG Reels 📸, GitHub ZIP 📦, Google Drive 📁\n"
        f"🎮 *3. Interactive Group Games:* Dice 🎲, Ludo 🎲, Dart 🎯, Basket 🏀, Football ⚽, Slot 🎰, Bowling 🎳, Couple ❤️\n"
        f"🤖 *4. Jarvis AI Remote Control:* Remote control Android Mobile & Windows PC\n"
        f"💥 *5. Group Utilities & Roasts:* Custom roasts/gali 💥, TagAll 🏷️, Auto Welcome 🎆, VC Logger 🎙️\n"
        f"⚡ *6. PC & Mobile Agents:* Includes `Jarvis-Mobile-Agent.apk` and PC `MARK-L.exe` server!\n\n"
        f"👇 *Click below to add the bot to your group with full admin permissions:*"
    )

    keyboard = [
        [InlineKeyboardButton("➕ Add Bot to Telegram Group", url=add_group_url)],
        [InlineKeyboardButton("📲 Share with Friends", callback_data="menu_share")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def share_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    bot_username = await get_bot_username(context)

    share_text = (
        f"🚀 Check out @{bot_username} - The Ultimate Telegram Music, Downloader, Games & Jarvis Remote Bot! 🎧\n\n"
        f"✨ Features included:\n"
        f"🎵 Play any song, Phonk & Beats in high quality\n"
        f"📥 Download YouTube 1080p, IG Reels, GitHub & GDrive\n"
        f"🎮 Play Ludo, Dice, Dart, Football, Slot & Bowling\n"
        f"🤖 Control Android Phone & PC remotely (Jarvis APK & PC MARK-L.exe!)\n\n"
        f"👉 Start now: https://t.me/{bot_username}"
    )
    encoded_share = urllib.parse.quote(share_text)
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}&text={encoded_share}"

    text = (
        f"📲 *SHARE TELEGRAM MUSIC & JARVIS BOT WITH FRIENDS* 🌟\n\n"
        f"Send this bot to your friends and groups so everyone can enjoy free music, video downloads, interactive games & remote PC/mobile control!\n\n"
        f"📌 *All Features Included:* \n"
        f"• 🎵 Unlimited Music, Phonk & Beats Player\n"
        f"• 📥 YouTube 1080p & Social Video Downloader\n"
        f"• 🎮 Native Telegram Games (Ludo, Dice, Dart, Slot, Bowling)\n"
        f"• 🤖 Jarvis Remote Agent (Mobile APK & PC `MARK-L.exe` included)\n"
        f"• 💥 Fun Roasts, TagAll, Welcome & Group Utilities\n\n"
        f"👇 *Click below to choose a friend or group to share:*"
    )

    keyboard = [
        [InlineKeyboardButton("📲 Share Bot with Friends", url=share_url)],
        [InlineKeyboardButton("➕ Add Bot to Group", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)

    keyboard = []
    for code, name in config.SUPPORTED_LANGUAGES.items():
        prefix = "✅ " if code == lang else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{name}", callback_data=f"setlang_{code}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])

    text = get_text(lang, "lang_select")
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    lang_code = query.data.replace("setlang_", "")
    if lang_code not in config.SUPPORTED_LANGUAGES:
        await query.answer("Invalid language selection.", show_alert=True)
        return
    db.set_user_language(query.from_user.id, lang_code)
    
    text = get_text(lang_code, "lang_updated")
    try:
        await query.edit_message_text(text, parse_mode="Markdown")
    except Exception:
        await query.message.reply_text(text, parse_mode="Markdown")
    await start_command(update, context)

async def owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    safe_owner = escape_md(config.OWNER_USERNAME)
    text = get_text(lang, "owner_info", owner=safe_owner)
    owner_clean = config.OWNER_USERNAME.replace("@", "")

    keyboard = [
        [InlineKeyboardButton(f"💬 Chat with Owner ({config.OWNER_USERNAME})", url=f"https://t.me/{owner_clean}")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    msg = update.message

    # Handle active WhatsApp recipient/prompt setup before other text workflows.
    from handlers.whatsapp import handle_whatsapp_text
    if await handle_whatsapp_text(update, context):
        return

    # 1. Ignore automatic channel post forwards in discussion groups!
    if getattr(msg, "is_automatic_forward", False) or getattr(msg, "auto_forward", False):
        return

    # 2. Ignore channel posts forwarded into discussion groups
    if msg.sender_chat and msg.sender_chat.type == "channel":
        return

    # 3. Ignore service messages (new member joins, title change, pins)
    if msg.new_chat_members or msg.left_chat_member or msg.group_chat_created or msg.supergroup_chat_created:
        return

    chat_type = update.effective_chat.type if update.effective_chat else "private"
    is_group = chat_type in ["group", "supergroup"]

    text = msg.text.strip()
    if not text:
        return

    # Force Subscribe Check in Private Chats (Must Join @cosmic_jarvis & @cosmic_setion)
    if not is_group:
        from services.force_sub import check_user_joined_all, get_force_sub_keyboard, get_force_sub_text
        is_joined, missing = await check_user_joined_all(context.bot, msg.from_user.id, msg.from_user.username)
        if not is_joined:
            await msg.reply_text(
                get_force_sub_text(msg.from_user.first_name, missing),
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=get_force_sub_keyboard()
            )
            return

    # Check Cloud Storage conversational state (phone, OTP, 2FA, group name, text notes)
    from handlers.cloud_storage import handle_cloud_storage_text, cloud_storage_command
    if await handle_cloud_storage_text(update, context):
        return

    from handlers.music import music_command, pp_command, pb_command, process_and_send_song
    from handlers.ai_assistant import ai_command
    from handlers.premium import handle_premium_text
    from handlers.premium_tools import handle_premium_tool_text
    from handlers.search_hub import handle_search_hub_text

    if await handle_premium_tool_text(update, context):
        return
    if await handle_premium_text(update, context):
        return
    if await handle_search_hub_text(update, context):
        return

    # Check button text matches (multilingual support)
    if any(k in text for k in ["Telegram Group", "Cloud Storage", "क्लाउड स्टोरेज", "टेलीग्राम ग्रुप"]):
        await cloud_storage_command(update, context)
        return
    elif any(k in text for k in ["Study Mode", "Study", "पढ़ाई", "अभ्यास", "Notes", "Exam"]):
        from handlers.study import study_command
        await study_command(update, context)
    elif any(k in text for k in ["New Space Photos", "Latest Space Photos", "New Astronomy", "New Photo", "Space Photo", "नई फोटो"]):
        from handlers.astronomy import latest_astronomy_command
        await latest_astronomy_command(update, context)
    elif "APOD" in text or "Astronomy Picture" in text:
        from handlers.astronomy import apod_command
        await apod_command(update, context)
    elif "New Planets" in text or "Exoplanet" in text:
        from handlers.astronomy import planet_command
        await planet_command(update, context)
    elif "FunFact" in text or "Space FunFact" in text:
        from handlers.astronomy import fact_command
        await fact_command(update, context)
    elif "Asteroids" in text or "Near-Earth" in text:
        from handlers.astronomy import asteroids_command
        await asteroids_command(update, context)
    elif "Mars View" in text or "Mars Rover" in text:
        from handlers.astronomy import mars_command
        await mars_command(update, context)
    elif "Subscribe 24/7" in text or "Subscribe" in text:
        from handlers.astronomy import subscribe_command
        await subscribe_command(update, context)
    elif any(k in text for k in ["Music Hub", "म्यूजिक", "म्यूज़िक", "संगीत"]):
        await music_command(update, context)

    elif any(k in text.lower() for k in ["downloader", "download", "डाउनलोड"]):
        from bot import show_downloader_menu
        await show_downloader_menu(update, context)
    elif any(k in text.lower() for k in ["games", "गेम्स"]):
        from bot import show_games_menu
        await show_games_menu(update, context)
    elif any(k in text.lower() for k in ["fun", "roasts", "ग़ाली", "gali"]):
        from bot import show_extra_menu
        await show_extra_menu(update, context)
    elif any(k in text for k in ["Phonk", "फोनक"]):
        await pp_command(update, context)
    elif any(k in text for k in ["Beats", "बीट्स"]):
        await pb_command(update, context)
    elif any(k in text for k in ["AI Tune", "AI धुन", "Tune Finder"]):
        await ai_command(update, context)
    elif any(k in text for k in ["Add to Group", "ग्रुप में", "group"]):
        await add_group_command(update, context)
    elif any(k in text for k in ["Share", "दोस्तों को", "भेजें"]):
        await share_bot_command(update, context)
    elif any(k in text for k in ["Language", "भाषा"]):
        await language_command(update, context)
    elif any(k in text for k in ["Help", "हेल्प", "गाइड"]):
        await help_command(update, context)
    elif any(k in text for k in ["Owner", "मालिक"]):
        await owner_command(update, context)
    elif text.startswith("http://") or text.startswith("https://"):
        from handlers.downloader import download_command
        context.args = [text]
        await download_command(update, context)
    else:
        # In Private Chats: direct text typing searches songs.
        if not is_group:
            await process_and_send_song(update, context, text, category="direct_text")
