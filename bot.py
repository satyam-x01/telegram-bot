import asyncio
import sys
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import config
from database import db
from locales import get_text
from handlers.start import (
    start_command,
    help_command,
    add_group_command,
    share_bot_command,
    language_command,
    language_callback,
    owner_command,
    text_message_handler
)
from handlers.music import (
    music_command,
    psname_command,
    pp_command,
    pb_command,
    aisinger_command,
    music_callback_handler
)
from handlers.ai_assistant import ai_command, voice_note_handler
from handlers.jarvis import jarvis_command, jarvis_callback_handler
from handlers.premium import (
    premium_command,
    premium_enter_code,
    premium_codes_command,
    redeem_command,
    generate_and_send_codes,
)
from handlers.search_hub import (
    choose_search_mode,
    quick_search_command,
    search_hub_command,
)
from handlers.premium_tools import choose_premium_tool, show_premium_tools
from handlers.admin import admin_command, stats_command, broadcast_command, dev_command
from handlers.astronomy import (
    apod_command,
    latest_astronomy_command,
    jwst_command,
    search_command,
    planet_command,
    fact_command,
    asteroids_command,
    mars_command,
    subscribe_command,
    unsubscribe_command,
    astronomy_callback_handler
)
from handlers.study import study_command, study_callback_router
from handlers.cloud_storage import (
    cloud_storage_command,
    cloud_storage_callback_handler,
    handle_cloud_storage_media,
    set_api_command
)
from handlers.whatsapp import whatsapp_command, whatsapp_entry_callback, whatsapp_callback
from services.nasa_service import nasa_service
from services.ai_service import ai_service
import random

from handlers.games import (
    dice_command,
    dart_command,
    basketball_command,
    football_command,
    slot_command,
    bowling_command,
    ludo_command,
    couple_command,
    love_command
)
from handlers.fun_extra import (
    tagall_command,
    gali_command,
    galigif_command,
    wish_command,
    welcome_command,
    vclogs_command,
    telegraph_command,
    bots_command,
    markdown_command
)
from handlers.admin_adv import (
    auth_command,
    unauth_command,
    gban_command,
    ungban_command,
    blchat_command,
    unblchat_command,
    cplay_command,
    maintenance_command,
    ping_command,
    speed_command,
    reload_command
)
from handlers.music_control import (
    play_command,
    lastwave_command,
    webplay_command,
    vplay_command,
    pause_command,
    resume_command,
    skip_command,
    end_command,
    queue_command,
    loop_command,
    shuffle_command,
    seek_command,
    song_command,
    playlist_command,
    addplaylist_command,
    delplaylist_command
)
from handlers.downloader import (
    download_command,
    yt_command,
    yt_quality_callback_handler,
    insta_command,
    github_command,
    gdrive_command,
    pinterest_command,
    pinterest_callback_handler
)
from services.downloader_service import downloader_service
from services.public_download import public_download_service



logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def web_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quick_search_command(update, context, "web")


async def telegram_bot_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quick_search_command(update, context, "tgbot")


async def telegram_channel_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quick_search_command(update, context, "tgchannel")


async def telegram_group_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quick_search_command(update, context, "tggroup")

broadcast_cycle_index = 0

async def hourly_astronomy_broadcast(context: ContextTypes.DEFAULT_TYPE):
    """24/7 Hourly automated space broadcast function running every 1 hour (3600s).
    Cycles 1 category per hour:
      - Hour 1: 📸 1️⃣ NASA ASTRONOMY PICTURE OF THE DAY (with Photo & Complete Info)
      - Hour 2: 💡 2️⃣ MIND-BLOWING ASTRONOMY FUN FACT
      - Hour 3: 🪐 3️⃣ EXOPLANET & SPACE DISCOVERY SPOTLIGHT (with Photo & Complete Info)
    """
    global broadcast_cycle_index

    subscribers = db.get_all_subscriptions()
    if not subscribers:
        return

    current_mode = broadcast_cycle_index % 3
    broadcast_cycle_index += 1

    if current_mode == 0:
        # ─── HOUR 1: NASA ASTRONOMY PICTURE OF THE DAY (LATEST & NEWEST) ───
        apod_data = nasa_service.get_apod()
        if not apod_data or apod_data.get("media_type") != "image":
            # If today's APOD is unavailable or video, pick the newest recent image APOD
            recent_apods = nasa_service.get_recent_apods(limit=3)
            if recent_apods:
                apod_data = recent_apods[0]

        if not apod_data:
            return

        title = apod_data.get("title", "Astronomy Picture of the Day")
        date = apod_data.get("date", "")
        explanation = apod_data.get("explanation", "")
        url = apod_data.get("url", "")
        hdurl = apod_data.get("hdurl", url)
        media_type = apod_data.get("media_type", "image")
        copyright_info = apod_data.get("copyright", "NASA")

        short_exp = explanation[:650] + "..." if len(explanation) > 650 else explanation

        caption = (
            f"📸 *1️⃣ NASA ASTRONOMY PICTURE OF THE DAY*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📅 *Date:* `{date}`\n"
            f"📌 *Title:* {title}\n"
            f"👤 *Credit:* {copyright_info}\n\n"
            f"📝 *Complete Information:*\n{short_exp}\n\n"
            f"✨ [View High-Res HD Image]({hdurl})"
        )

        keyboard = [
            [
                InlineKeyboardButton("✨ HD Full Image", url=hdurl) if hdurl else InlineKeyboardButton("🪐 Discover Exoplanets", callback_data="astro_planet"),
                InlineKeyboardButton("☄️ Near-Earth Asteroids", callback_data="astro_asteroids")
            ],
            [
                InlineKeyboardButton("🔴 Mars Rover View", callback_data="astro_mars"),
                InlineKeyboardButton("🔍 AI Space Search", switch_inline_query_current_chat="/search ")
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        for chat_id in subscribers:
            try:
                if url and media_type == "image":
                    try:
                        await context.bot.send_photo(chat_id=chat_id, photo=url, caption=caption, parse_mode="Markdown", reply_markup=markup)
                        continue
                    except Exception as e:
                        logger.warning(f"Error sending APOD photo to {chat_id}: {e}")

                await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode="Markdown", disable_web_page_preview=False, reply_markup=markup)
            except Exception as e:
                logger.warning(f"Error broadcasting APOD to {chat_id}: {e}")

    elif current_mode == 1:
        # ─── HOUR 2: MIND-BLOWING ASTRONOMY FUN FACT ───
        fact_data = ai_service.generate_hourly_funfact()
        title = fact_data.get("title", "🌌 Mind-Blowing Astronomy Fact")
        fact = fact_data.get("fact", "")
        topic = fact_data.get("topic", "Astronomy")

        text = (
            f"💡 *2️⃣ MIND-BLOWING ASTRONOMY FUN FACT*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{title}\n"
            f"📌 *Topic:* `{topic}`\n\n"
            f"✨ {fact}"
        )

        keyboard = [
            [
                InlineKeyboardButton("🪐 Exoplanets Catalog", callback_data="astro_planet"),
                InlineKeyboardButton("☄️ Near-Earth Asteroids", callback_data="astro_asteroids")
            ],
            [
                InlineKeyboardButton("🔍 AI Space Search", switch_inline_query_current_chat="/search ")
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        for chat_id in subscribers:
            try:
                await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=markup)
            except Exception as e:
                logger.warning(f"Error broadcasting fact to {chat_id}: {e}")

    elif current_mode == 2:
        # ─── HOUR 3: EXOPLANET & SPACE DISCOVERY SPOTLIGHT (WITH PHOTO) ───
        exoplanets = nasa_service.get_exoplanet_catalog()
        planet = random.choice(exoplanets)
        planet_img = planet.get("image")

        caption = (
            f"🪐 *3️⃣ EXOPLANET & SPACE DISCOVERY SPOTLIGHT*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⭐ *Planet Name:* `{planet['name']}`\n"
            f"📏 *Distance from Earth:* {planet['distance']}\n"
            f"⭐ *Host Star:* {planet['star']}\n"
            f"🧪 *Classification:* {planet['type']}\n"
            f"🚀 *Discovery:* {planet['discovered']}\n\n"
            f"💡 *Scientific Details & Key Fact:*\n{planet['fact']}"
        )

        keyboard = [
            [
                InlineKeyboardButton("🌌 Today's APOD Photo", callback_data="astro_apod"),
                InlineKeyboardButton("🔴 Mars Rover View", callback_data="astro_mars")
            ],
            [
                InlineKeyboardButton("🔍 AI Space Search", switch_inline_query_current_chat="/search ")
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        for chat_id in subscribers:
            try:
                if planet_img:
                    try:
                        await context.bot.send_photo(chat_id=chat_id, photo=planet_img, caption=caption, parse_mode="Markdown", reply_markup=markup)
                        continue
                    except Exception as e:
                        logger.warning(f"Error sending exoplanet photo to {chat_id}: {e}")

                await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode="Markdown", reply_markup=markup)
            except Exception as e:
                logger.warning(f"Error broadcasting exoplanet to {chat_id}: {e}")

async def show_games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    """Show Games Category Menu"""
    text = (
        "🎮 *TELEGRAM NATIVE INTERACTIVE GAMES* 🎯\n\n"
        "• `/dice` : Roll a dice 🎲\n"
        "• `/ludo` : Play Ludo 🎲\n"
        "• `/dart` : Throw a dart 🎯\n"
        "• `/basket` or `/basketball` : Play Basketball 🏀\n"
        "• `/football` : Play Football ⚽\n"
        "• `/slot` or `/jackpot` : Play Jackpot Slot Machine 🎰\n"
        "• `/bowling` : Play Bowling 🎳\n"
        "• `/couple` : Pick Couple of the Day ❤️\n"
        "• `/love` : Love Match Percentage 💘"
    )
    keyboard = [
        [InlineKeyboardButton("🎲 Roll Dice", callback_data="btn_game_dice"), InlineKeyboardButton("🎯 Throw Dart", callback_data="btn_game_dart")],
        [InlineKeyboardButton("🏀 Basketball", callback_data="btn_game_basket"), InlineKeyboardButton("⚽ Football", callback_data="btn_game_football")],
        [InlineKeyboardButton("🎰 Slot Jackpot", callback_data="btn_game_slot"), InlineKeyboardButton("🎳 Bowling", callback_data="btn_game_bowling")],
        [InlineKeyboardButton("🎲 Ludo Roll", callback_data="btn_game_ludo"), InlineKeyboardButton("❤️ Couple of the Day", callback_data="btn_game_couple")],
        [InlineKeyboardButton("💘 Love Match", callback_data="btn_game_love")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_extra_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Fun & Extra Commands Category Menu (Screenshot 2)"""
    text = "💥 *FUN & EXTRA GROUP UTILITIES* 🌟\n\nSelect a category below to explore commands:"
    keyboard = [
        [InlineKeyboardButton("💥 GALI", callback_data="btn_gali"), InlineKeyboardButton("🎬 GALI GIF", callback_data="btn_galigif")],
        [InlineKeyboardButton("🤖 BOTS", callback_data="btn_bots"), InlineKeyboardButton("✨ WISH TAG", callback_data="btn_wish")],
        [InlineKeyboardButton("👋 WELCOME", callback_data="btn_welcome"), InlineKeyboardButton("📡 RTMPS LIVE", callback_data="btn_vclogs")],
        [InlineKeyboardButton("💕 LOVE BIRDS", callback_data="btn_game_love"), InlineKeyboardButton("🎙️ VC LOGS", callback_data="btn_vclogs")],
        [InlineKeyboardButton("👩‍❤️‍👨 COUPLE OF THE DAY", callback_data="btn_game_couple")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_main")]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Admin & Governance Menu (Screenshot 4)"""
    text = "⚡ *ALL ADMIN & GOVERNANCE COMMANDS WORK WITH:* `/`"
    keyboard = [
        [InlineKeyboardButton("🔧 ADMIN", callback_data="admin_stats"), InlineKeyboardButton("🔐 AUTH", callback_data="btn_auth_info")],
        [InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast_help"), InlineKeyboardButton("🛑 BL-CHAT", callback_data="btn_blchat_info")],
        [InlineKeyboardButton("🚫 BL-USERS", callback_data="btn_bluser_info"), InlineKeyboardButton("📻 C-PLAY", callback_data="btn_cplay_info"), InlineKeyboardButton("🔨 G-BAN", callback_data="btn_gban_info")],
        [InlineKeyboardButton("🔁 LOOP", callback_data="btn_loop_info"), InlineKeyboardButton("🛠️ MAINTENANCE", callback_data="btn_maint_info"), InlineKeyboardButton("🏓 PING", callback_data="btn_ping_info")],
        [InlineKeyboardButton("🥂 CLOSE", callback_data="close_menu")]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_music_control_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Music Control Help Panel (Screenshot 3)"""
    text = "CLICK A BUTTON BELOW TO LEARN MORE ABOUT A COMMAND:"
    keyboard = [
        [InlineKeyboardButton("🎵 /play", callback_data="help_play"), InlineKeyboardButton("📹 /vplay", callback_data="help_vplay"), InlineKeyboardButton("🔄 /reload", callback_data="help_reload")],
        [InlineKeyboardButton("⏸️ /pause", callback_data="help_pause"), InlineKeyboardButton("⏹️ /end", callback_data="help_end"), InlineKeyboardButton("⏭️ /skip", callback_data="help_skip")],
        [InlineKeyboardButton("🌐 /lang", callback_data="help_lang"), InlineKeyboardButton("🎶 /queue", callback_data="help_queue"), InlineKeyboardButton("🔁 /loop", callback_data="help_loop")],
        [InlineKeyboardButton("🎧 /vclogger", callback_data="help_vclogger"), InlineKeyboardButton("🏓 /ping", callback_data="help_ping"), InlineKeyboardButton("🛑 CLOSE", callback_data="close_menu")]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_features_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show All Features Submenu (Screenshot 5)"""
    text = "✨ *TELEGRAM MUSIC BOT FEATURES MENU* ✨\n\nTap any category to explore:"
    keyboard = [
        [InlineKeyboardButton("🎵 PLAY", callback_data="help_play"), InlineKeyboardButton("🔀 SHUFFLE", callback_data="btn_shuffle_info")],
        [InlineKeyboardButton("⏩ SEEK", callback_data="btn_seek_info"), InlineKeyboardButton("📥 SONG", callback_data="btn_song_info")],
        [InlineKeyboardButton("⚡ SPEED", callback_data="btn_ping_info"), InlineKeyboardButton("📜 POLICY", callback_data="btn_policy_info"), InlineKeyboardButton("🎮 GAMES", callback_data="menu_games")],
        [InlineKeyboardButton("🚫 BANS", callback_data="btn_gban_info"), InlineKeyboardButton("📝 TELEGRAPH", callback_data="btn_telegraph"), InlineKeyboardButton("🏷️ TAGS", callback_data="btn_tags_info")],
        [InlineKeyboardButton("🔙 BACK", callback_data="menu_main")]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_downloader_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Universal Downloader Category Menu"""
    text = (
        "📥 *UNIVERSAL MEDIA & FILE DOWNLOADER HUB* ⚡\n\n"
        "Download content from YouTube, Instagram, GitHub & Google Drive directly in Telegram!\n\n"
        "📌 *Available Commands & Usage:*\n"
        "• `/yt <link>` : YouTube 1080p, 720p, 480p, 360p MP4 & MP3\n"
        "• `/insta <link>` : Instagram Reels, IGTV & Photos\n"
        "• `/github <link>` : GitHub Repo Source Code ZIP Archive\n"
        "• `/gdrive <link>` : Google Drive Files, Videos & Music\n\n"
        "💡 *Tip:* Send or paste any link directly into the chat!"
    )
    keyboard = [
        [InlineKeyboardButton("🎬 YouTube Downloader", callback_data="btn_dl_yt_info"), InlineKeyboardButton("📸 Instagram Reel", callback_data="btn_dl_insta_info")],
        [InlineKeyboardButton("📦 GitHub ZIP Archive", callback_data="btn_dl_github_info"), InlineKeyboardButton("📁 Google Drive Files", callback_data="btn_dl_gdrive_info")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from utils import check_group_admin_permission
    if not await check_group_admin_permission(update, context):
        return

    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    data = query.data or ""

    if data == "wa_entry":
        await whatsapp_entry_callback(update, context)
    elif data.startswith("wa_"):
        await whatsapp_callback(update, context)
    elif data.startswith("cs_"):
        await cloud_storage_callback_handler(update, context)
    elif data.startswith("astro_"):
        await astronomy_callback_handler(update, context)
    elif data.startswith("st_") or data == "noop":
        await study_callback_router(update, context)
    elif data in ["menu_main", "main_menu"]:
        await start_command(update, context)

    elif data in ["menu_music", "music_hub"]:
        await music_command(update, context)
    elif data in ["menu_downloader", "downloader_hub"]:
        await show_downloader_menu(update, context)
    elif data in ["menu_help", "help_panel"] or data.startswith("help_page_"):
        await help_command(update, context)
    elif data == "menu_games":
        await show_games_menu(update, context)
    elif data == "menu_extra":
        await show_extra_menu(update, context)
    elif data in ["menu_admin", "admin_panel"]:
        await show_admin_menu(update, context)
    elif data == "menu_features":
        await show_features_menu(update, context)
    elif data == "close_menu":
        try:
            await query.message.delete()
        except Exception:
            pass
    elif data == "check_fsub":
        user = update.effective_user
        from services.force_sub import check_user_joined_all, get_force_sub_keyboard, get_force_sub_text
        is_joined, missing = await check_user_joined_all(context.bot, user.id, user.username)
        if is_joined:
            try:
                await query.answer("🎉 Verification Successful! Bot Unlocked!", show_alert=True)
            except Exception:
                pass
            await start_command(update, context)
        else:
            missing_names = "\n• ".join([ch["name"] for ch in missing])
            try:
                await query.answer(f"❌ Abhi tak join nahi hua:\n• {missing_names}\n\nKripya pehle dono channels join karein!", show_alert=True)
            except Exception:
                pass
            try:
                await query.edit_message_text(
                    get_force_sub_text(user.first_name, missing),
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                    reply_markup=get_force_sub_keyboard()
                )
            except Exception:
                pass
    elif data == "menu_addgroup":
        await add_group_command(update, context)
    elif data == "menu_share":
        await share_bot_command(update, context)
    elif data == "menu_lang":
        await language_command(update, context)
    elif data == "menu_owner":
        await owner_command(update, context)
    elif data in ["menu_ai", "ai_song_finder"]:
        await ai_command(update, context)
    elif data == "premium_menu":
        await premium_command(update, context)
    elif data == "premium_enter_code":
        await premium_enter_code(update, context)
    elif data == "premium_export_codes":
        await generate_and_send_codes(update, context)
    elif data == "premium_tools":
        await show_premium_tools(update, context)
    elif data.startswith("premium_tool_"):
        await choose_premium_tool(update, context)
    elif data == "search_hub":
        await search_hub_command(update, context)
    elif data.startswith("search_mode_"):
        await choose_search_mode(update, context)
    elif data.startswith("btn_jarvis_"):
        await jarvis_callback_handler(update, context)
    elif data in ["btn_start_nova", "start_nova"]:
        await startnova_command(update, context)
    elif data == "btn_stop_nova":
        db.disconnect_jarvis(update.effective_user.id)
        await query.message.reply_text("🛑 *NOVA 5-Minute Session Stopped.*", parse_mode="Markdown")
    elif data == "ignore":
        pass

    elif data.startswith("setlang_"):
        await language_callback(update, context)

    # Game Callbacks
    elif data == "btn_game_dice":
        await dice_command(update, context)
    elif data == "btn_game_dart":
        await dart_command(update, context)
    elif data == "btn_game_basket":
        await basketball_command(update, context)
    elif data == "btn_game_football":
        await football_command(update, context)
    elif data == "btn_game_slot":
        await slot_command(update, context)
    elif data == "btn_game_bowling":
        await bowling_command(update, context)
    elif data == "btn_game_ludo":
        await ludo_command(update, context)
    elif data == "btn_game_couple":
        await couple_command(update, context)
    elif data == "btn_game_love":
        await love_command(update, context)

    # Fun & Extra Callbacks
    elif data in ["btn_gali", "btn_another_gali"]:
        await gali_command(update, context)
    elif data == "btn_galigif":
        await galigif_command(update, context)
    elif data == "btn_bots":
        await bots_command(update, context)
    elif data == "btn_markdown":
        await markdown_command(update, context)
    elif data == "btn_wish":
        await wish_command(update, context)
    elif data == "btn_welcome":
        await welcome_command(update, context)
    elif data == "btn_vclogs":
        await vclogs_command(update, context)
    elif data == "btn_telegraph":
        await telegraph_command(update, context)

    # Admin Help Callbacks
    elif data == "btn_auth_info":
        await query.message.reply_text("🔐 *AUTH COMMANDS*\n\nUse `/auth` (reply to user) to authorize members to control music.\nUse `/unauth` to revoke authorization.", parse_mode="Markdown")
    elif data == "btn_gban_info":
        await query.message.reply_text("🔨 *G-BAN COMMANDS*\n\nUse `/gban <user_id>` to globally ban toxic users.\nUse `/ungban <user_id>` to remove global ban.", parse_mode="Markdown")
    elif data == "btn_blchat_info":
        await query.message.reply_text("🛑 *BL-CHAT COMMANDS*\n\nUse `/blchat` to blacklist current group chat.\nUse `/unblchat` to unblacklist.", parse_mode="Markdown")
    elif data == "btn_bluser_info":
        await query.message.reply_text("🚫 *BL-USERS COMMANDS*\n\nUse `/block <user_id>` to block user.\nUse `/unblock <user_id>` to unblock user.", parse_mode="Markdown")
    elif data == "btn_cplay_info":
        await query.message.reply_text("📻 *C-PLAY COMMANDS*\n\nUse `/cplay <channel_username>` to link channel music streaming to group.", parse_mode="Markdown")
    elif data == "btn_maint_info":
        await query.message.reply_text("🛠️ *MAINTENANCE MODE*\n\nUse `/maintenance` as bot owner to toggle maintenance mode on/off.", parse_mode="Markdown")
    elif data == "btn_ping_info":
        await ping_command(update, context)
    elif data == "btn_loop_info":
        await query.message.reply_text("🔁 *LOOP COMMAND*\n\nUse `/loop` to toggle single track loop or queue loop.", parse_mode="Markdown")
    elif data == "btn_shuffle_info":
        await query.message.reply_text("🔀 *SHUFFLE COMMAND*\n\nUse `/shuffle` to randomize music queue.", parse_mode="Markdown")
    elif data == "btn_seek_info":
        await query.message.reply_text("⏩ *SEEK COMMAND*\n\nUse `/seek <timestamp>` (e.g. `/seek 01:20`) to jump to a specific part in track.", parse_mode="Markdown")
    elif data == "btn_song_info":
        await query.message.reply_text("📥 *SONG COMMAND*\n\nUse `/song <song_name>` to download MP3 track.", parse_mode="Markdown")
    elif data == "btn_tags_info":
        await tagall_command(update, context)
    elif data == "btn_policy_info":
        await query.message.reply_text("📜 *PRIVACY & TERMS POLICY*\n\nTelegram Music Bot respects user privacy. No audio data or private messages are recorded.", parse_mode="Markdown")

    # Help Panel Specific Button Handlers (Screenshot 3)
    elif data == "help_play":
        await query.message.reply_text("🎵 **/play Command Help**\n\nFormat: `/play <song name>`\nPlays high quality audio in Telegram Music Player.", parse_mode="Markdown")
    elif data == "help_vplay":
        await query.message.reply_text("📹 **/vplay Command Help**\n\nFormat: `/vplay <video song name>`\nPlays video music stream in Telegram.", parse_mode="Markdown")
    elif data == "help_reload":
        await reload_command(update, context)
    elif data == "help_pause":
        await pause_command(update, context)
    elif data == "help_end":
        await end_command(update, context)
    elif data == "help_skip":
        await skip_command(update, context)
    elif data == "help_lang":
        await language_command(update, context)
    elif data == "help_queue":
        await queue_command(update, context)
    elif data == "help_loop":
        await loop_command(update, context)
    elif data == "help_vclogger":
        await vclogs_command(update, context)
    elif data == "help_ping":
        await ping_command(update, context)

    # Playlist Callbacks
    elif data.startswith("addpl_"):
        song_title = data.replace("addpl_", "").strip()
        user_id = query.from_user.id
        db.add_to_playlist(user_id, song_title, song_title)
        try:
            await query.answer("❤️ Added to your Personal Playlist!", show_alert=True)
        except Exception:
            pass
    elif data == "btn_view_playlist":
        await playlist_command(update, context)
    elif data.startswith("playpl_"):
        try:
            idx = int(data.replace("playpl_", ""))
            user_id = query.from_user.id
            pl = db.get_user_playlist(user_id)
            if pl and idx < len(pl):
                target_song = pl[idx]["query"] or pl[idx]["song_title"]
                from handlers.music import process_and_send_song
                await process_and_send_song(update, context, target_song, category="playlist_play")
        except Exception as e:
            print(f"Error playing playlist song: {e}")
    elif data == "btn_clear_playlist":
        user_id = query.from_user.id
        db.clear_user_playlist(user_id)
        try:
            await query.answer("🧹 Playlist Cleared!", show_alert=True)
        except Exception:
            pass
        await playlist_command(update, context)
    elif data == "btn_addpl_help":
        await query.message.reply_text("💡 *How to add songs to Playlist:*\n\nType `/addplaylist <song name>` or tap `❤️ Add to Playlist` on any song sent by the bot!", parse_mode="Markdown")

    elif (
        data.startswith("play_")
        or data.startswith("genre_")
        or data.startswith("mlang_")
        or data.startswith("msinger_")
        or data.startswith("msong_")
        or data.startswith("page_")
        or data in ["search_singer", "another_singer", "search_song", "another_song"]
    ):
        await music_callback_handler(update, context)
    elif data.startswith("yt_dl_"):
        await yt_quality_callback_handler(update, context)
    elif data.startswith("pin_dl_"):
        await pinterest_callback_handler(update, context)
    elif data in ["btn_dl_pin_info", "btn_dl_pinterest_info"]:
        await query.message.reply_text(
            "📌 *PINTEREST DOWNLOADER*\n\n"
            "Download photos, videos & music directly from Pinterest!\n\n"
            "• `/pin <url>` or `/pinterest <url>`\n"
            "• Example: `/pin https://pin.it/example`\n"
            "• Supports HD photos, videos (MP4) & music (MP3) extraction!",
            parse_mode="Markdown"
        )

    elif data == "admin_stats":
        await admin_command(update, context)
    elif data == "admin_broadcast_help":
        await query.answer("Use /broadcast <message> in chat as owner", show_alert=True)
    else:
        try:
            await query.answer("Option selected", show_alert=False)
        except Exception:
            pass

async def post_init(application):
    try:
        bot_info = await application.bot.get_me()
        config.BOT_USERNAME = bot_info.username
        print(f"🤖 Telegram Bot Username verified: @{config.BOT_USERNAME}")
    except Exception as e:
        print(f"Could not fetch bot username at startup: {e}")
    try:
        await asyncio.to_thread(public_download_service.start)
    except Exception as e:
        print(f"⚠️ Direct HTTPS download setup failed: {e}")

async def post_shutdown(application):
    await asyncio.to_thread(public_download_service.stop)

def main():
    token = config.BOT_TOKEN
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or token == "your_bot_token_here":
        print("\n" + "=" * 60)
        print("⚠️ TELEGRAM BOT TOKEN IS MISSING!")
        print("Please edit the '.env' file in this folder and add your TELEGRAM_BOT_TOKEN.")
        print("Get your bot token free from @BotFather on Telegram.")
        print("=" * 60 + "\n")
        sys.exit(1)

    try:
        print(f"📹 {downloader_service.prepare_large_video_support()}")
    except Exception as e:
        print(f"⚠️ Large-video support setup failed: {e}")
        print("The bot will continue, but large videos may not split/upload correctly.")

    print("🚀 Initializing Telegram Music Bot...")
    print(f"👑 Owner Username configured as: {config.OWNER_USERNAME}")

    request = HTTPXRequest(
        connection_pool_size=32,
        connect_timeout=20.0,
        read_timeout=120.0,
        write_timeout=120.0,
        pool_timeout=20.0,
        httpx_kwargs={"verify": False}
    )
    app = ApplicationBuilder().token(token).request(request).post_init(post_init).post_shutdown(post_shutdown).build()
    from utils import check_group_admin_permission

    def add_cmd(command_name, handler_func):
        async def guarded_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not await check_group_admin_permission(update, context):
                return
            return await handler_func(update, context)
        app.add_handler(CommandHandler(command_name, guarded_handler))

    # Register Basic & Help Handlers
    add_cmd("start", start_command)
    add_cmd("help", help_command)
    add_cmd("study", study_command)
    add_cmd("exam", study_command)
    add_cmd("exams", study_command)
    add_cmd("notes", study_command)
    add_cmd("music", music_command)
    add_cmd("addgroup", add_group_command)
    add_cmd("share", share_bot_command)
    add_cmd("language", language_command)
    add_cmd("lanuage", language_command)
    add_cmd("jarvis", jarvis_command)
    add_cmd("premium", premium_command)
    add_cmd("redeem", redeem_command)
    add_cmd("premiumcodes", premium_codes_command)
    add_cmd("premiumtools", show_premium_tools)
    add_cmd("searchhub", search_hub_command)
    add_cmd("web", web_search_command)
    add_cmd("botsearch", telegram_bot_search_command)
    add_cmd("channelsearch", telegram_channel_search_command)
    add_cmd("groupsearch", telegram_group_search_command)

    # Register Music Play & Search Commands
    add_cmd("play", play_command)
    add_cmd("lastwave", lastwave_command)
    add_cmd("webplay", webplay_command)
    add_cmd("vplay", vplay_command)
    add_cmd("psname", psname_command)
    add_cmd("aisinger", aisinger_command)
    add_cmd("pp", pp_command)
    add_cmd("phonk", pp_command)
    add_cmd("pb", pb_command)
    add_cmd("beats", pb_command)
    add_cmd("pause", pause_command)
    add_cmd("resume", resume_command)
    add_cmd("skip", skip_command)
    add_cmd("end", end_command)
    add_cmd("stop", end_command)
    add_cmd("queue", queue_command)
    add_cmd("loop", loop_command)
    add_cmd("shuffle", shuffle_command)
    add_cmd("song", song_command)
    add_cmd("playlist", playlist_command)
    add_cmd("addplaylist", addplaylist_command)
    add_cmd("delplaylist", delplaylist_command)

    # Register Games Commands
    add_cmd("dice", dice_command)
    add_cmd("dart", dart_command)
    add_cmd("basket", basketball_command)
    add_cmd("basketball", basketball_command)
    add_cmd("football", football_command)
    add_cmd("slot", slot_command)
    add_cmd("jackpot", slot_command)
    add_cmd("bowling", bowling_command)
    add_cmd("ludo", ludo_command)
    add_cmd("couple", couple_command)
    add_cmd("love", love_command)

    # Register Fun & Extra Commands
    add_cmd("tagall", tagall_command)
    add_cmd("all", tagall_command)
    add_cmd("gali", gali_command)
    add_cmd("galigif", galigif_command)
    add_cmd("gali_gif", galigif_command)
    add_cmd("gifgali", galigif_command)
    add_cmd("spamgali", gali_command)
    add_cmd("multigali", gali_command)
    add_cmd("wish", wish_command)
    add_cmd("welcome", welcome_command)
    add_cmd("vclogs", vclogs_command)
    add_cmd("telegraph", telegraph_command)
    add_cmd("bots", bots_command)
    add_cmd("markdown", markdown_command)

    # Register Downloader Commands
    add_cmd("download", download_command)
    add_cmd("dl", download_command)
    add_cmd("yt", yt_command)
    add_cmd("youtube", yt_command)
    add_cmd("insta", insta_command)
    add_cmd("instagram", insta_command)
    add_cmd("reel", insta_command)
    add_cmd("reels", insta_command)
    add_cmd("github", github_command)
    add_cmd("git", github_command)
    add_cmd("gdrive", gdrive_command)
    add_cmd("drive", gdrive_command)
    add_cmd("pin", pinterest_command)
    add_cmd("pinterest", pinterest_command)

    # Register Admin & Governance Commands
    add_cmd("auth", auth_command)
    add_cmd("unauth", unauth_command)
    add_cmd("gban", gban_command)
    add_cmd("ungban", ungban_command)
    add_cmd("blchat", blchat_command)
    add_cmd("unblchat", unblchat_command)
    add_cmd("block", gban_command)
    add_cmd("unblock", ungban_command)
    add_cmd("cplay", cplay_command)
    add_cmd("maintenance", maintenance_command)
    add_cmd("ping", ping_command)
    add_cmd("speed", speed_command)
    add_cmd("reload", reload_command)
    add_cmd("vlogger", vclogs_command)

    # Register AI Commands
    add_cmd("ai", ai_command)
    add_cmd("ai_song", ai_command)
    add_cmd("tune", ai_command)
    add_cmd("findsong", ai_command)

    # Register Astronomy & NASA Commands
    add_cmd("latest", latest_astronomy_command)
    add_cmd("spacephoto", latest_astronomy_command)
    add_cmd("astrophoto", latest_astronomy_command)
    add_cmd("newphoto", latest_astronomy_command)
    add_cmd("jwst", jwst_command)
    add_cmd("apod", apod_command)
    add_cmd("search", search_command)
    add_cmd("planet", planet_command)
    add_cmd("exoplanet", planet_command)
    add_cmd("exoplanets", planet_command)
    add_cmd("funfact", fact_command)
    add_cmd("fact", fact_command)
    add_cmd("asteroids", asteroids_command)
    add_cmd("neo", asteroids_command)
    add_cmd("mars", mars_command)
    add_cmd("subscribe", subscribe_command)
    add_cmd("unsubscribe", unsubscribe_command)

    # Register Study, Exam & Educational Hub Commands
    add_cmd("study", study_command)
    add_cmd("exam", study_command)
    add_cmd("exams", study_command)
    add_cmd("notes", study_command)

    # Owner & Admin Core Commands
    add_cmd("owner", owner_command)
    add_cmd("admin", admin_command)
    add_cmd("stats", stats_command)
    add_cmd("broadcast", broadcast_command)
    add_cmd("dev", dev_command)

    # Register Cloud Storage & Telegram Group Commands
    add_cmd("cloud", cloud_storage_command)
    add_cmd("storage", cloud_storage_command)
    add_cmd("telegram_group", cloud_storage_command)
    add_cmd("tgroup", cloud_storage_command)
    add_cmd("setapi", set_api_command)
    add_cmd("whatsapp", whatsapp_command)

    # Callback Query Router
    app.add_handler(CallbackQueryHandler(callback_router))

    # Media Handler for Cloud Storage (Photos, Videos, Documents)
    async def guarded_cloud_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await handle_cloud_storage_media(update, context)

    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, guarded_cloud_media))

    # Voice Note Handler for AI tune identification
    async def guarded_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await check_group_admin_permission(update, context):
            return
        return await voice_note_handler(update, context)

    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, guarded_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    # Clean up any leftover song downloads from disk on launch
    from utils import purge_all_downloads
    purge_all_downloads()

    print("🚀 Telegram Music, Downloader, Cloud Storage & Jarvis Bot is running! Press Ctrl+C to stop.\n")
    app.run_polling()


if __name__ == "__main__":
    main()
