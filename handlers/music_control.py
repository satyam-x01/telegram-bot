import asyncio
import os
import urllib.parse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.music import process_and_send_song, send_audio_result
from services.music_service import music_service
from database import db
from locales import get_text
from utils import escape_md

# Global memory queue for music player per chat
MUSIC_QUEUES = {}
PLAYER_STATE = {}

async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/play command handler"""
    if not context.args:
        await update.message.reply_text("📌 *Usage:* `/play <song name or link>`\n\nExample: `/play Kesariya`", parse_mode="Markdown")
        return
    query = " ".join(context.args)
    await process_and_send_song(update, context, query, category="play_cmd")

async def lastwave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/lastwave <song name> opens the official YouTube track link."""
    if not context.args:
        await update.message.reply_text(
            "📌 Usage: `/lastwave <song name>`\nExample: `/lastwave Kesariya`",
            parse_mode="Markdown",
        )
        return

    song_query = " ".join(context.args)
    status_msg = await update.message.reply_text("🔎 Searching for the official track link...")
    result = await asyncio.to_thread(music_service.fast_get_video_id, song_query)
    if not result or not result.get("video_id"):
        await status_msg.edit_text(f"❌ No track found for: {escape_md(song_query)}", parse_mode="Markdown")
        return

    track_url = f"https://www.youtube.com/watch?v={result['video_id']}"
    title = result.get("title") or song_query
    artist = result.get("uploader") or ""
    await status_msg.edit_text(
        f"🎵 *{escape_md(title)}*\n"
        f"👤 {escape_md(artist)}\n\n"
        "Open the official track link. On Android, LastWave may open it if it is installed and set to handle YouTube links.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("▶️ Open track", url=track_url)
        ]]),
    )

async def webplay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/webplay <authorized direct audio URL> [title]"""
    player_base_url = os.getenv("PLAYER_BASE_URL", "").strip().rstrip("/")
    if not player_base_url:
        await update.message.reply_text(
            "⚠️ Web player is not configured. Set PLAYER_BASE_URL to your Cloudflare Pages URL in the Railway service variables."
        )
        return

    try:
        parsed_base = urllib.parse.urlsplit(player_base_url)
    except ValueError:
        parsed_base = None
    if not parsed_base or parsed_base.scheme != "https" or not parsed_base.netloc:
        await update.message.reply_text("⚠️ PLAYER_BASE_URL must be a valid HTTPS URL.")
        return

    if not context.args:
        await update.message.reply_text(
            "📌 Usage: `/webplay <authorized direct audio URL> [track title]`\n"
            "Example: `/webplay https://example.com/your-own-track.mp3 My Track`\n\n"
            "Use only audio you own or are authorized to stream.",
            parse_mode="Markdown",
        )
        return

    audio_url = context.args[0].strip()
    try:
        parsed_audio = urllib.parse.urlsplit(audio_url)
    except ValueError:
        parsed_audio = None
    if (
        not parsed_audio
        or parsed_audio.scheme not in {"http", "https"}
        or not parsed_audio.netloc
        or len(audio_url) > 2000
    ):
        await update.message.reply_text("❌ Please provide a valid HTTP or HTTPS direct audio URL.")
        return

    title = " ".join(context.args[1:]).strip()[:160]
    query = urllib.parse.urlencode({"audio": audio_url, "title": title})
    player_url = f"{player_base_url}/?{query}"
    await update.message.reply_text(
        f"🎵 {escape_md(title or 'Audio track')}\nOpen the player and press Play. Only use authorized audio.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("▶️ Open player", url=player_url)
        ]]),
    )

async def vplay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/vplay video music command handler"""
    if not context.args:
        await update.message.reply_text("📌 *Usage:* `/vplay <video song name>`\n\nExample: `/vplay Starboy Official Video`", parse_mode="Markdown")
        return
    query = " ".join(context.args)
    await process_and_send_song(update, context, query, category="vplay_cmd")

async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/pause command handler"""
    chat_id = update.effective_chat.id
    PLAYER_STATE[chat_id] = "paused"
    text = "⏸️ *Music Playback Paused.*\n\nUse `/resume` to continue listening!"
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")

async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/resume command handler"""
    chat_id = update.effective_chat.id
    PLAYER_STATE[chat_id] = "playing"
    text = "▶️ *Music Playback Resumed!* Enjoy your tunes 🎵"
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")

async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/skip command handler"""
    chat_id = update.effective_chat.id
    q = MUSIC_QUEUES.get(chat_id, [])
    if q and len(q) > 0:
        next_song = q.pop(0)
        await update.message.reply_text(f"⏭️ *Skipped! Playing next track:* `{escape_md(next_song)}`", parse_mode="Markdown")
        await process_and_send_song(update, context, next_song, category="queue")
    else:
        await update.message.reply_text("⏭️ *Skipped! No more tracks in queue.* Use `/play <song>` to add songs!", parse_mode="Markdown")

async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/end or /stop command handler"""
    chat_id = update.effective_chat.id
    MUSIC_QUEUES[chat_id] = []
    PLAYER_STATE[chat_id] = "stopped"
    text = "⏹️ *Music Playback Stopped & Queue Cleared!* 🧹"
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")

async def queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/queue command handler"""
    chat_id = update.effective_chat.id
    q = MUSIC_QUEUES.get(chat_id, [])
    if not q:
        q_text = "🎶 *Music Queue is currently empty!*\n\nAdd songs with `/play <song name>`"
    else:
        items = "\n".join([f"{i+1}. `{escape_md(s)}`" for i, s in enumerate(q[:10])])
        q_text = f"🎶 *CURRENT MUSIC QUEUE* ({len(q)} Songs):\n\n{items}"
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_music")]]
    if update.message:
        await update.message.reply_text(q_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text(q_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def loop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/loop command handler"""
    chat_id = update.effective_chat.id
    current_loop = PLAYER_STATE.get(f"loop_{chat_id}", "off")
    next_loop = "single" if current_loop == "off" else ("queue" if current_loop == "single" else "off")
    PLAYER_STATE[f"loop_{chat_id}"] = next_loop

    mode_str = "🔂 Single Track Loop" if next_loop == "single" else ("🔁 Full Queue Loop" if next_loop == "queue" else "➡️ Loop Disabled")
    await update.message.reply_text(f"🔁 *Loop Mode Changed:* {mode_str}", parse_mode="Markdown")

async def shuffle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/shuffle command handler"""
    import random
    chat_id = update.effective_chat.id
    q = MUSIC_QUEUES.get(chat_id, [])
    if q:
        random.shuffle(q)
        MUSIC_QUEUES[chat_id] = q
        await update.message.reply_text(f"🔀 *Music Queue Shuffled!* ({len(q)} songs randomized)", parse_mode="Markdown")
    else:
        await update.message.reply_text("🔀 *Queue is empty! Nothing to shuffle.*", parse_mode="Markdown")

async def seek_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/seek command handler"""
    timestamp = " ".join(context.args) if context.args else "00:30"
    safe_ts = escape_md(timestamp)
    await update.message.reply_text(f"⏩ *Seeked track to timestamp:* `{safe_ts}`", parse_mode="Markdown")

async def song_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/song download command handler"""
    if not context.args:
        await update.message.reply_text("📌 *Usage:* `/song <song name>`\n\nExample: `/song Kesariya`", parse_mode="Markdown")
        return
    query = " ".join(context.args)
    await process_and_send_song(update, context, query, category="song_download")

async def playlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/playlist view and play command handler"""
    user_id = update.effective_user.id
    user_name = escape_md(update.effective_user.first_name)
    pl = db.get_user_playlist(user_id)

    if not pl:
        text = (
            f"📜 *YOUR PERSONAL MUSIC PLAYLIST* 🎵\n\n"
            f"Hello {user_name}! Your playlist is currently empty.\n\n"
            f"💡 *How to add songs:*\n"
            f"• Use `/addplaylist <song name>` (e.g. `/addplaylist Kesariya`)\n"
            f"• Or tap `❤️ Add to Playlist` on any song sent by the bot!"
        )
        keyboard = [[InlineKeyboardButton("🎵 Open Music Hub", callback_data="menu_music")]]
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    text = f"📜 *{user_name}'s PERSONAL PLAYLIST* ({len(pl)} Songs) 🎵\n\nTap any song below to play instantly in Telegram:"
    keyboard = []

    # Display top songs as 1-tap play buttons
    top_pl = pl[:8]
    for idx, item in enumerate(top_pl):
        stitle = item["song_title"]
        keyboard.append([InlineKeyboardButton(f"▶️ {stitle}", callback_data=f"playpl_{idx}")])

    keyboard.append([
        InlineKeyboardButton("➕ Add Song", callback_data="btn_addpl_help"),
        InlineKeyboardButton("🧹 Clear Playlist", callback_data="btn_clear_playlist")
    ])
    keyboard.append([InlineKeyboardButton("🔙 Back to Music Hub", callback_data="menu_music")])

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def addplaylist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/addplaylist command handler"""
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("📌 *Usage:* `/addplaylist <song name>`\n\nExample: `/addplaylist Kesariya`", parse_mode="Markdown")
        return

    song_name = " ".join(context.args).strip()
    db.add_to_playlist(user_id, song_name, song_name)
    safe_name = escape_md(song_name)
    await update.message.reply_text(f"❤️ *Added to your Playlist:* `{safe_name}` ✨\n\nUse `/playlist` to view your collection!", parse_mode="Markdown")

async def delplaylist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/delplaylist command handler"""
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("📌 *Usage:* `/delplaylist <song name>`", parse_mode="Markdown")
        return

    song_name = " ".join(context.args).strip()
    db.remove_from_playlist(user_id, song_name)
    safe_name = escape_md(song_name)
    await update.message.reply_text(f"🗑️ *Removed from your Playlist:* `{safe_name}`", parse_mode="Markdown")
