import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from database import db
from locales import get_text
from services.music_service import music_service
from utils import escape_md
from music_catalog import MUSIC_LANGUAGES, SINGERS_CATALOG, get_singers_for_lang, get_singer_details
from handlers.cloud_storage import get_add_to_group_button

async def music_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    text = (
        "🎧 *Music Hub & All Language Categories* 🎶\n\n"
        "Select your preferred *Music Language or Genre* to explore top hit singers & songs!"
    )

    from handlers.start import get_bot_username
    import urllib.parse
    bot_username = await get_bot_username(context)
    add_group_url = f"https://t.me/{bot_username}?startgroup=true"
    share_text = get_text(lang, "share_text")
    encoded_share = urllib.parse.quote(share_text)
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}&text={encoded_share}"

    keyboard = [
        [
            InlineKeyboardButton("🇮🇳 Hindi Hits", callback_data="mlang_hindi"),
            InlineKeyboardButton("🎶 Punjabi Beats", callback_data="mlang_punjabi")
        ],
        [
            InlineKeyboardButton("🇬🇧 English & US", callback_data="mlang_english"),
            InlineKeyboardButton("🇲🇽 Spanish Pop", callback_data="mlang_spanish")
        ],
        [
            InlineKeyboardButton("🇰🇷 K-Pop Hits", callback_data="mlang_kpop"),
            InlineKeyboardButton("🎬 Bhojpuri Pop", callback_data="mlang_bhojpuri")
        ],
        [
            InlineKeyboardButton("💥 Haryanvi Hits", callback_data="mlang_haryanvi"),
            InlineKeyboardButton("⚡ Tamil Hits", callback_data="mlang_tamil")
        ],
        [
            InlineKeyboardButton("🔥 Telugu Hits", callback_data="mlang_telugu"),
            InlineKeyboardButton("🌴 Malayalam Hits", callback_data="mlang_malayalam")
        ],
        [
            InlineKeyboardButton("🎧 Kannada Hits", callback_data="mlang_kannada"),
            InlineKeyboardButton("🚩 Marathi Hits", callback_data="mlang_marathi")
        ],
        [
            InlineKeyboardButton("🕺 Gujarati Hits", callback_data="mlang_gujarati"),
            InlineKeyboardButton("🎨 Bengali Hits", callback_data="mlang_bengali")
        ],
        [
            InlineKeyboardButton("🌙 Urdu & Ghazals", callback_data="mlang_urdu"),
            InlineKeyboardButton("🕌 Arabic Hits", callback_data="mlang_arabic")
        ],
        [
            InlineKeyboardButton("🏎️ Phonk Tracks", callback_data="mlang_phonk"),
            InlineKeyboardButton("☕ Chill Beats & Lo-Fi", callback_data="mlang_beats")
        ],
        [
            InlineKeyboardButton(get_text(lang, "btn_add_group"), url=add_group_url),
            InlineKeyboardButton(get_text(lang, "btn_share_bot"), url=share_url)
        ],
        [
            InlineKeyboardButton("🤖 AI Song Finder", callback_data="menu_ai"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")
        ]
    ]

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def psname_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)

    if not context.args:
        usage_msg = (
            "📌 *Usage of /psname command:*\n\n"
            "Format: `/psname <song name>`\n\n"
            "💡 *Examples:*\n"
            "• `/psname Kesariya` (Hindi)\n"
            "• `/psname Starboy` (English)\n"
            "• `/psname 295 Sidhu Moose Wala` (Punjabi)\n"
            "• `/psname Brazilian Phonk` (Phonk)"
        )
        await update.message.reply_text(usage_msg, parse_mode="Markdown")
        return

    song_query = " ".join(context.args)
    await process_and_send_song(update, context, song_query, category="search")

async def pp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    subgenre = " ".join(context.args) if context.args else ""
    
    status_msg = await update.message.reply_text("🔥 *Fetching top Phonk track...*", parse_mode="Markdown")
    track_info = await music_service.get_phonk_track(subgenre)
    
    if track_info:
        await send_audio_result(update, context, status_msg, track_info, category="phonk")
    else:
        err_msg = get_text(lang, "song_not_found", query=escape_md(f"Phonk {subgenre}".strip()))
        await status_msg.edit_text(err_msg, parse_mode="Markdown")

async def pb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    subgenre = " ".join(context.args) if context.args else ""

    status_msg = await update.message.reply_text("🎧 *Fetching top Beats / Lo-Fi track...*", parse_mode="Markdown")
    track_info = await music_service.get_beats_track(subgenre)

    if track_info:
        await send_audio_result(update, context, status_msg, track_info, category="beats")
    else:
        err_msg = get_text(lang, "song_not_found", query=escape_md(f"Beats {subgenre}".strip()))
        await status_msg.edit_text(err_msg, parse_mode="Markdown")

async def process_and_send_song(update: Update, context: ContextTypes.DEFAULT_TYPE, song_query: str, category: str = "general"):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    safe_query = escape_md(song_query)

    msg_text = get_text(lang, "searching", query=safe_query)
    if update.message:
        status_msg = await update.message.reply_text(msg_text, parse_mode="Markdown")
    elif update.callback_query:
        status_msg = await update.callback_query.message.reply_text(msg_text, parse_mode="Markdown")
    else:
        return

    # Instant send from Telegram file_id cache if query matches
    cached = db.get_cached_audio(song_query)
    if cached and cached.get("file_id"):
        try:
            await status_msg.edit_text("⚡ *Sending cached track instantly...*", parse_mode="Markdown")
            title = escape_md(cached["title"])
            artist = escape_md(cached["artist"])
            owner = escape_md(config.OWNER_USERNAME)
            caption = (
                f"🎵 *{title}*\n"
                f"👤 *Artist:* {artist}\n"
                f"🤖 *Bot by:* {owner}"
            )
            cached_kb = [
                [
                    InlineKeyboardButton("❤️ Add to Playlist", callback_data=f"addpl_{cached['title'][:25]}"),
                    InlineKeyboardButton("📜 My Playlist", callback_data="btn_view_playlist")
                ],
                [
                    get_add_to_group_button("music")
                ]
            ]
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=cached["file_id"],
                title=cached["title"],
                performer=cached["artist"],
                duration=int(cached.get("duration") or 0),
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(cached_kb)
            )
            db.log_play(user_id, cached["title"], category)
            await status_msg.delete()
            return
        except Exception as cache_err:
            print(f"Cached file_id failed, fallback to downloading: {cache_err}")

    # Fast 0.3s check by video_id before initiating full download
    import asyncio
    loop = asyncio.get_event_loop()
    fast_meta = await loop.run_in_executor(None, music_service.fast_get_video_id, song_query)
    if fast_meta and fast_meta.get("video_id"):
        v_id = fast_meta["video_id"]
        cached_v = db.get_cached_audio(v_id)
        if cached_v and cached_v.get("file_id"):
            try:
                await status_msg.edit_text("⚡ *Sending cached track instantly...*", parse_mode="Markdown")
                title = escape_md(cached_v["title"])
                artist = escape_md(cached_v["artist"])
                owner = escape_md(config.OWNER_USERNAME)
                caption = (
                    f"🎵 *{title}*\n"
                    f"👤 *Artist:* {artist}\n"
                    f"🤖 *Bot by:* {owner}"
                )
                cached_v_kb = [
                    [
                        InlineKeyboardButton("❤️ Add to Playlist", callback_data=f"addpl_{cached_v['title'][:25]}"),
                        InlineKeyboardButton("📜 My Playlist", callback_data="btn_view_playlist")
                    ],
                    [
                        get_add_to_group_button("music")
                    ]
                ]
                await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=cached_v["file_id"],
                    title=cached_v["title"],
                    performer=cached_v["artist"],
                    duration=int(cached_v.get("duration") or 0),
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(cached_v_kb)
                )
                db.save_audio_cache(song_query, cached_v["file_id"], cached_v["title"], cached_v["artist"], cached_v.get("duration") or 0)
                db.log_play(user_id, cached_v["title"], category)
                await status_msg.delete()
                return
            except Exception as cache_err:
                print(f"Cached video_id failed: {cache_err}")

    dl_text = get_text(lang, "downloading", title=safe_query)
    await status_msg.edit_text(dl_text, parse_mode="Markdown")

    track_info = await music_service.download_audio(song_query)

    if track_info:
        await send_audio_result(update, context, status_msg, track_info, category=category, query_key=song_query)
    else:
        err_msg = get_text(lang, "song_not_found", query=safe_query)
        await status_msg.edit_text(err_msg, parse_mode="Markdown")

async def send_audio_result(update: Update, context: ContextTypes.DEFAULT_TYPE, status_msg, track_info: dict, category: str, query_key: str = ""):
    user_id = update.effective_user.id
    filepath = track_info.get('filepath')
    raw_title = track_info.get('title', 'Unknown Title')
    raw_artist = track_info.get('artist', 'Unknown Artist')
    duration = track_info.get('duration', 0)
    video_id = track_info.get('video_id')

    title = escape_md(raw_title)
    artist = escape_md(raw_artist)
    owner = escape_md(config.OWNER_USERNAME)

    try:
        await status_msg.edit_text("🎵 *Loading track into Telegram Music Player...*", parse_mode="Markdown")
        
        with open(filepath, 'rb') as audio_file:
            caption = (
                f"🎵 *{title}*\n"
                f"👤 *Artist:* {artist}\n"
                f"🤖 *Bot by:* {owner}"
            )
            keyboard = [
                [
                    InlineKeyboardButton("❤️ Add to Playlist", callback_data=f"addpl_{raw_title[:25]}"),
                    InlineKeyboardButton("📜 My Playlist", callback_data="btn_view_playlist")
                ],
                [
                    get_add_to_group_button("music")
                ]
            ]
            sent_msg = await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=audio_file,
                title=raw_title,
                performer=raw_artist,
                duration=int(duration),
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                read_timeout=120,
                write_timeout=120,
                connect_timeout=60
            )
        
        # Save Telegram file_id to database cache for instant future sends
        if sent_msg and sent_msg.audio and sent_msg.audio.file_id:
            file_id = sent_msg.audio.file_id
            if query_key:
                db.save_audio_cache(query_key, file_id, raw_title, raw_artist, duration)
            if raw_title:
                db.save_audio_cache(raw_title, file_id, raw_title, raw_artist, duration)
            if video_id:
                db.save_audio_cache(video_id, file_id, raw_title, raw_artist, duration)

        # Log play to database
        db.log_play(user_id, raw_title, category)
        await status_msg.delete()
    except Exception as e:
        print(f"Error sending audio: {e}")
        safe_err = escape_md(str(e))
        try:
            await status_msg.edit_text(f"❌ *Failed to send audio:* {safe_err}", parse_mode="Markdown")
        except Exception:
            await status_msg.edit_text(f"❌ Failed to send audio: {e}")
    finally:
        # Cleanup file after sending to preserve disk space
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

async def aisinger_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    if not context.args:
        prompt_msg = (
            "🎤 *AI Singer Search*\n\n"
            "Format: `/aisinger <singer name or song>`\n\n"
            "💡 *Examples:*\n"
            "• `/aisinger Arijit Singh`\n"
            "• `/aisinger KK`\n"
            "• `/aisinger Sidhu Moose Wala`\n"
            "• `/aisinger The Weeknd`"
        )
        await update.message.reply_text(prompt_msg, parse_mode="Markdown")
        return

    singer_query = " ".join(context.args).strip()
    safe_singer = escape_md(singer_query)

    # Match in catalog first (singer name or song title match)
    matched_singer = None
    matched_lang_key = None
    matched_song_idx = None

    q_lower = singer_query.lower()

    for lang_k, s_list in SINGERS_CATALOG.items():
        for s in s_list:
            s_name = s['name'].lower()
            if q_lower in s_name or s_name in q_lower:
                matched_singer = s
                matched_lang_key = lang_k
                break
            # Check if query matches a song in this singer's catalog
            for idx, song_title in enumerate(s['songs']):
                if q_lower in song_title.lower() or song_title.lower() in q_lower:
                    matched_singer = s
                    matched_lang_key = lang_k
                    matched_song_idx = idx
                    break
            if matched_singer:
                break
        if matched_singer:
            break

    # If specific song matched directly in catalog, play it instantly!
    if matched_singer and matched_song_idx is not None:
        song_name = matched_singer['songs'][matched_song_idx]
        full_query = f"{song_name} by {matched_singer['name']}"
        await process_and_send_song(update, context, full_query, category="ai_singer_direct")
        return

    if matched_singer:
        lang_k = matched_lang_key
        s = matched_singer
        safe_name = escape_md(s['name'])
        lang_info = MUSIC_LANGUAGES.get(lang_k, {"name": lang_k.title()})
        safe_lang = escape_md(lang_info['name'])
        res_text = (
            f"🎤 *Artist Found: {safe_name}*\n"
            f"📁 *Category:* {safe_lang}\n\n"
            f"👇 *Tap any top hit song below to play instantly:* "
        )
        
        songs = s['songs']
        keyboard = []
        top_songs = songs[:6]
        for i in range(0, len(top_songs), 2):
            row = [InlineKeyboardButton(f"▶️ {top_songs[i]}", callback_data=f"msong_{lang_k}_{s['id']}_{i}")]
            if i + 1 < len(top_songs):
                row.append(InlineKeyboardButton(f"▶️ {top_songs[i+1]}", callback_data=f"msong_{lang_k}_{s['id']}_{i+1}"))
            keyboard.append(row)

        keyboard.append([
            InlineKeyboardButton("📄 View All Hits", callback_data=f"msinger_{lang_k}_{s['id']}"),
            InlineKeyboardButton("🔍 Other Singer", callback_data="search_singer")
        ])
        keyboard.append([InlineKeyboardButton("🔙 Back to Music Hub", callback_data="menu_music")])
        await update.message.reply_text(res_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        status_msg = await update.message.reply_text(f"🔎 *Searching top tracks for `{safe_singer}`...*", parse_mode="Markdown")
        await process_and_send_song(update, context, f"{singer_query} song", category="ai_singer")

async def music_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    data = query.data

    try:
        from handlers.start import get_bot_username
        import urllib.parse
        bot_username = await get_bot_username(context)
        add_group_url = f"https://t.me/{bot_username}?startgroup=true"
        lang = db.get_user_language(query.from_user.id)
        share_text = get_text(lang, "share_text")
        encoded_share = urllib.parse.quote(share_text)
        share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}&text={encoded_share}"

        if data in ["search_singer", "another_singer"]:
            prompt = (
                "🎤 *Search Singer / Artist*\n\n"
                "Type singer name directly into chat (e.g. `Arijit Singh`, `KK`) or use:\n"
                "`/aisinger <singer name>`"
            )
            keyboard = [[InlineKeyboardButton("🔙 Back to Music Hub", callback_data="menu_music")]]
            await query.message.reply_text(prompt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

        elif data in ["search_song", "another_song"]:
            prompt = (
                "🎵 *Search Any Song*\n\n"
                "Type song name directly into chat (e.g. `Kesariya`, `Starboy`) or use:\n"
                "`/psname <song name>`"
            )
            keyboard = [[InlineKeyboardButton("🔙 Back to Music Hub", callback_data="menu_music")]]
            await query.message.reply_text(prompt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

        elif data == "play_phonk":
            status_msg = await query.message.reply_text("🔥 *Fetching top Phonk track...*", parse_mode="Markdown")
            track_info = await music_service.get_phonk_track()
            if track_info:
                await send_audio_result(update, context, status_msg, track_info, category="phonk")
            else:
                await status_msg.edit_text("❌ Could not fetch Phonk track.")

        elif data == "play_beats":
            status_msg = await query.message.reply_text("🎧 *Fetching top Beats track...*", parse_mode="Markdown")
            track_info = await music_service.get_beats_track()
            if track_info:
                await send_audio_result(update, context, status_msg, track_info, category="beats")
            else:
                await status_msg.edit_text("❌ Could not fetch Beats track.")

        elif data.startswith("mlang_") or data.startswith("page_singers_"):
            if data.startswith("page_singers_"):
                parts = data.split("_")
                lang_key = parts[2]
                page_num = int(parts[3])
            else:
                lang_key = data.replace("mlang_", "")
                page_num = 1

            singers = get_singers_for_lang(lang_key)
            lang_info = MUSIC_LANGUAGES.get(lang_key, {"name": lang_key.title(), "flag": "🎵"})
            safe_lang_name = escape_md(lang_info['name'])

            PAGE_SIZE = 6
            total_singers = len(singers)
            total_pages = max(1, (total_singers + PAGE_SIZE - 1) // PAGE_SIZE)
            page_num = max(1, min(page_num, total_pages))

            start_idx = (page_num - 1) * PAGE_SIZE
            current_singers = singers[start_idx:start_idx + PAGE_SIZE]

            text = f"🎤 *Popular Singers & Artists in {safe_lang_name}*\n\nSelect a singer to view their trending hit songs (Page {page_num}/{total_pages}):"
            keyboard = []
            for i in range(0, len(current_singers), 2):
                row = [InlineKeyboardButton(f"👤 {current_singers[i]['name']}", callback_data=f"msinger_{lang_key}_{current_singers[i]['id']}")]
                if i + 1 < len(current_singers):
                    row.append(InlineKeyboardButton(f"👤 {current_singers[i+1]['name']}", callback_data=f"msinger_{lang_key}_{current_singers[i+1]['id']}"))
                keyboard.append(row)

            if total_pages > 1:
                nav_row = []
                if page_num > 1:
                    nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page_singers_{lang_key}_{page_num-1}"))
                nav_row.append(InlineKeyboardButton(f"📄 {page_num}/{total_pages}", callback_data="ignore"))
                if page_num < total_pages:
                    nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_singers_{lang_key}_{page_num+1}"))
                keyboard.append(nav_row)

            keyboard.append([InlineKeyboardButton("🔎 Search Another Singer", callback_data="search_singer")])
            keyboard.append([
                InlineKeyboardButton(get_text(lang, "btn_add_group"), url=add_group_url),
                InlineKeyboardButton(get_text(lang, "btn_share_bot"), url=share_url)
            ])
            keyboard.append([InlineKeyboardButton("🔙 Back to All Languages", callback_data="menu_music")])

            try:
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception:
                await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

        elif data.startswith("msinger_search_"):
            parts = data.split("_")
            if len(parts) >= 4:
                lang_key = parts[2]
                singer_id = parts[3]
                singer = get_singer_details(lang_key, singer_id)
                singer_name = singer["name"] if singer else "Singer"
                safe_name = escape_md(singer_name)
                prompt_text = (
                    f"✍️ *Search Any Other Song of {safe_name}*\n\n"
                    f"List me song nahi mila? No problem!\n"
                    f"Bas song ka naam directly chat me type karein (e.g. `{singer_name} song name`) ya use karein:\n"
                    f"`/psname {singer_name} <song name>`"
                )
                await query.message.reply_text(prompt_text, parse_mode="Markdown")

        elif data.startswith("msinger_") or data.startswith("page_songs_"):
            if data.startswith("page_songs_"):
                parts = data.split("_")
                lang_key = parts[2]
                singer_id = parts[3]
                page_num = int(parts[4])
            else:
                parts = data.split("_")
                lang_key = parts[1]
                singer_id = parts[2]
                page_num = 1

            singer = get_singer_details(lang_key, singer_id)

            if singer:
                safe_singer_name = escape_md(singer["name"])
                songs = singer["songs"]
                PAGE_SIZE = 6
                total_songs = len(songs)
                total_pages = max(1, (total_songs + PAGE_SIZE - 1) // PAGE_SIZE)
                page_num = max(1, min(page_num, total_pages))

                start_idx = (page_num - 1) * PAGE_SIZE
                current_songs = songs[start_idx:start_idx + PAGE_SIZE]

                text = f"🎵 *Top Trending Songs of {safe_singer_name}* ({total_songs} Hits - Page {page_num}/{total_pages})\n\nTap any song below to play directly in Telegram:"
                keyboard = []
                for idx_offset, song in enumerate(current_songs):
                    actual_idx = start_idx + idx_offset
                    keyboard.append([InlineKeyboardButton(f"▶️ {song}", callback_data=f"msong_{lang_key}_{singer_id}_{actual_idx}")])

                if total_pages > 1:
                    nav_row = []
                    if page_num > 1:
                        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page_songs_{lang_key}_{singer_id}_{page_num-1}"))
                    nav_row.append(InlineKeyboardButton(f"📄 {page_num}/{total_pages}", callback_data="ignore"))
                    if page_num < total_pages:
                        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_songs_{lang_key}_{singer_id}_{page_num+1}"))
                    keyboard.append(nav_row)

                keyboard.append([InlineKeyboardButton(f"🔍 Search Any Other Song of {singer['name']}", callback_data=f"msinger_search_{lang_key}_{singer_id}")])
                keyboard.append([
                    InlineKeyboardButton(get_text(lang, "btn_add_group"), url=add_group_url),
                    InlineKeyboardButton(get_text(lang, "btn_share_bot"), url=share_url)
                ])
                keyboard.append([InlineKeyboardButton(f"🔙 Back to Singers List", callback_data=f"mlang_{lang_key}")])

                try:
                    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
                except Exception:
                    await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

        elif data.startswith("msong_"):
            parts = data.split("_")
            if len(parts) >= 4:
                lang_key = parts[1]
                singer_id = parts[2]
                song_idx = int(parts[3])
                singer = get_singer_details(lang_key, singer_id)

                if singer and song_idx < len(singer["songs"]):
                    song_name = singer["songs"][song_idx]
                    full_query = f"{song_name} by {singer['name']}"
                    await process_and_send_song(update, context, full_query, category="catalog")
    except Exception as e:
        print(f"Error in music_callback_handler: {e}")
        try:
            await query.message.reply_text(f"❌ *Callback error:* {escape_md(str(e))}", parse_mode="Markdown")
        except Exception:
            pass
