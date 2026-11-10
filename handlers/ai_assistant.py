import os
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from database import db
from locales import get_text
from services.ai_service import ai_service
from handlers.music import process_and_send_song
from utils import escape_md

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)

    # Check if command has arguments or is just clicking/typing command
    if update.message and context.args:
        user_query = " ".join(context.args)
        await process_ai_song_find(update, context, user_query)
        return

    guide = (
        "🤖 *AI Music, Phonk & Beats Tune Finder* 🎧\n\n"
        "*Pata nahi song / phonk / beats ka naam? No problem!*\n\n"
        "🎙️ **Option 1 — Voice Note (Mic):**\n"
        "Bas apni aawaz me song/phonk ki tune gungunayein (humming), lyrics bolein, ya audio recording bhejein!\n\n"
        "✍️ **Option 2 — Text Description:**\n"
        "Type command: `/ai <description>` or `/ai_song <description>`\n\n"
        "💡 *Examples:*\n"
        "• `/ai song jisme gadi ka whistle sound aur heavy bass hai`\n"
        "• `/ai romantic Arijit Singh song brahmastra movie`\n"
        "• `/ai viral reels drift phonk song with Japanese vocals`\n"
        "• `/ai lofi chill beats for study`"
    )
    keyboard = [
        [InlineKeyboardButton("🎵 Open Music Hub", callback_data="menu_music")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]
    ]

    if update.message:
        await update.message.reply_text(guide, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.edit_message_text(guide, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def process_ai_song_find(update: Update, context: ContextTypes.DEFAULT_TYPE, user_query: str):
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    is_dev = db.is_dev_user(user_id)
    is_premium = db.is_premium_user(user_id)

    # Enforce Daily AI Limit (4 songs per day per user, unlimited for verified developer/owner)
    ai_limit = 4
    current_usage = db.get_ai_usage_today(user_id)
    if not (is_dev or is_premium) and current_usage >= ai_limit:
        limit_msg = (
            f"⚠️ *Daily AI Tune Limit Reached ({current_usage}/{ai_limit} songs today)* 🛑\n\n"
            f"You have used all {ai_limit} AI tune finder searches for today.\n"
            f"💡 *Tip:* Use `/psname <song name>` for unlimited direct song searches!"
        )
        if update.message:
            await update.message.reply_text(limit_msg, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.reply_text(limit_msg, parse_mode="Markdown")
        return

    if not ai_service.enabled:
        msg = get_text(lang, "ai_no_key", owner=escape_md(config.OWNER_USERNAME))
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    thinking_msg = await update.message.reply_text(get_text(lang, "ai_thinking"), parse_mode="Markdown")

    # Gemini REST calls are blocking; run them outside Telegram's event loop so
    # other users and button clicks stay responsive on PC and Termux.
    res = await asyncio.to_thread(ai_service.identify_song_from_description, user_query)

    if res and res.get("found"):
        db.increment_ai_usage_today(user_id)
        song_title = res.get("song_title")
        artist = res.get("artist")
        search_query = res.get("search_query") or f"{song_title} {artist}"
        reason = res.get("reason", "Matched description.")

        safe_song = escape_md(f"{song_title} - {artist}")
        safe_reason = escape_md(reason)
        found_text = get_text(lang, "ai_found", song=safe_song, reason=safe_reason)
        await thinking_msg.edit_text(found_text, parse_mode="Markdown")

        # Automatically download and send song
        await process_and_send_song(update, context, search_query, category="ai_recommendation")
    else:
        # Automatic YouTube Fallback Search
        db.increment_ai_usage_today(user_id)
        safe_q = escape_md(user_query)
        await thinking_msg.edit_text(
            f"🔎 *AI Fallback Match:* Searching track for `{safe_q}`...\n🎵 Preparing music player...",
            parse_mode="Markdown"
        )
        await process_and_send_song(update, context, user_query, category="ai_fallback")

async def voice_note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice notes sent by user for AI tune identification."""
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    is_dev = db.is_dev_user(user_id)
    is_premium = db.is_premium_user(user_id)

    if not update.message.voice and not update.message.audio:
        return

    # Enforce Daily AI Limit (4 songs per day per user, unlimited for developer/owner)
    ai_limit = 4
    current_usage = db.get_ai_usage_today(user_id)
    if not (is_dev or is_premium) and current_usage >= ai_limit:
        limit_msg = (
            f"⚠️ *Daily AI Tune Limit Reached ({current_usage}/{ai_limit} songs today)* 🛑\n\n"
            f"You have used all {ai_limit} AI voice/tune finder searches for today.\n"
            f"💡 *Tip:* Use `/psname <song name>` for unlimited direct song searches!"
        )
        await update.message.reply_text(limit_msg, parse_mode="Markdown")
        return

    if not ai_service.enabled:
        await update.message.reply_text(get_text(lang, "ai_no_key", owner=escape_md(config.OWNER_USERNAME)), parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("🎙️ *Processing voice note tune with Gemini AI...*", parse_mode="Markdown")

    file_obj = await context.bot.get_file(update.message.voice.file_id if update.message.voice else update.message.audio.file_id)
    temp_path = config.DOWNLOAD_DIR / f"voice_{user_id}_{update.message.message_id}.ogg"
    await file_obj.download_to_drive(temp_path)

    try:
        res = await asyncio.to_thread(ai_service.identify_song_from_audio, str(temp_path))
        if res and res.get("found"):
            db.increment_ai_usage_today(user_id)
            song_title = res.get("song_title")
            artist = res.get("artist")
            search_query = res.get("search_query") or f"{song_title} {artist}"
            reason = res.get("reason", "Matched hummed tune/voice note.")

            safe_song = escape_md(f"{song_title} - {artist}")
            safe_reason = escape_md(reason)
            found_text = get_text(lang, "ai_found", song=safe_song, reason=safe_reason)
            await status_msg.edit_text(found_text, parse_mode="Markdown")

            await process_and_send_song(update, context, search_query, category="ai_voice_recommendation")
        else:
            await status_msg.edit_text(
                "🤔 *AI could not clearly identify the tune from your voice note.* Please try humming louder or using text command `/ai <description>`!",
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Voice processing error: {e}")
        safe_err = escape_md(str(e))
        await status_msg.edit_text(f"❌ *Error analyzing voice note:* {safe_err}", parse_mode="Markdown")
    finally:
        if temp_path.exists():
            try:
                os.remove(temp_path)
            except Exception:
                pass
