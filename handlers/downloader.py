import os
import re
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.downloader_service import downloader_service
from services.public_download import public_download_service
from utils import escape_md
from handlers.cloud_storage import get_add_to_group_button

PENDING_YT_URLS = {}
PENDING_PIN_URLS = {}
TELEGRAM_UPLOAD_SAFE_BYTES = 45 * 1024 * 1024


async def _direct_download_markup(filepath, filename=None):
    if not await public_download_service.wait_until_ready(timeout=45):
        return None
    link = public_download_service.create_link(filepath, filename=filename)
    if not link:
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬇️ Direct HTTPS Download", url=link)]])


async def _website_download_markup(filepath, user_id, title):
    if not await public_download_service.wait_until_ready(timeout=45):
        return None
    url = public_download_service.create_web_session("file", "", user_id, title=title, filepath=filepath)
    if not url:
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Play / Download on Website", url=url)]])

async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Universal Downloader command /download <url>"""
    url = context.args[0].strip() if context.args else None
    if not url and update.message and update.message.reply_to_message:
        url = update.message.reply_to_message.text or ""

    if not url or not (url.startswith("http://") or url.startswith("https://")):
        text = (
            "📥 *UNIVERSAL MEDIA & FILE DOWNLOADER* ⚡\n\n"
            "Download content from any supported platform directly to Telegram!\n\n"
            "📌 *Supported Platforms & Commands:*\n"
            "• `/yt <url>` : YouTube Video (1080p, 720p, 480p, 360p), Shorts & MP3\n"
            "• `/insta <url>` : Instagram Reels, IGTV, Photos & Posts\n"
            "• `/pin <url>` : Pinterest Videos, Photos & Music (MP3)\n"
            "• `/github <url>` : GitHub Repository ZIP, Releases & Source Files\n"
            "• `/gdrive <url>` : Google Drive Videos, Audio, Photos & Documents\n\n"
            "💡 *Usage Example:* `/download https://pin.it/example`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Auto-detect URL platform
    if "youtube.com" in url or "youtu.be" in url:
        await yt_command(update, context, input_url=url)
    elif "instagram.com" in url:
        await insta_command(update, context, input_url=url)
    elif "pinterest.com" in url or "pin.it" in url:
        await pinterest_command(update, context, input_url=url)
    elif "github.com" in url or "raw.githubusercontent.com" in url:
        await github_command(update, context, input_url=url)
    elif "drive.google.com" in url or "docs.google.com" in url:
        await gdrive_command(update, context, input_url=url)
    else:
        await yt_command(update, context, input_url=url)

async def yt_command(update: Update, context: ContextTypes.DEFAULT_TYPE, input_url: str = None):
    """YouTube Video, Shorts & MP3 Downloader with Quality Selector"""
    url = input_url or (context.args[0].strip() if context.args else None)
    if not url and update.message and update.message.reply_to_message:
        url = update.message.reply_to_message.text or ""

    if not url or not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ *Please provide a valid YouTube video or Shorts link!*\nExample: `/yt https://youtu.be/dQw4w9WgXcQ`", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("🔍 *Analyzing YouTube video metadata & quality options...*", parse_mode="Markdown")

    info = await downloader_service.get_yt_info(url)
    if not info:
        await status_msg.edit_text("❌ *Failed to retrieve YouTube video metadata. Please check the URL and try again!*", parse_mode="Markdown")
        return

    url_key = str(abs(hash(url)))[:10]
    PENDING_YT_URLS[url_key] = url

    title = escape_md(info['title'])
    duration_min = info['duration'] // 60
    duration_sec = info['duration'] % 60
    dur_str = f"{duration_min}:{duration_sec:02d}"

    text = (
        f"🎥 *YOUTUBE DOWNLOADER* ⚡\n\n"
        f"📌 *Title:* {title}\n"
        f"👤 *Channel:* {escape_md(info['uploader'])}\n"
        f"⏱️ *Duration:* `{dur_str}`\n\n"
        f"👇 *Select your preferred download format & quality:*🔻"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎬 1080p MP4", callback_data=f"yt_dl_1080_{url_key}"),
            InlineKeyboardButton("📺 720p MP4", callback_data=f"yt_dl_720_{url_key}")
        ],
        [
            InlineKeyboardButton("📱 480p MP4", callback_data=f"yt_dl_480_{url_key}"),
            InlineKeyboardButton("🎞️ 360p MP4", callback_data=f"yt_dl_360_{url_key}")
        ],
        [
            InlineKeyboardButton("🎵 MP3 Audio (Best)", callback_data=f"yt_dl_mp3_{url_key}")
        ],
    ]

    is_large = info.get("duration", 0) > 180 or info.get("estimated_size", 0) > TELEGRAM_UPLOAD_SAFE_BYTES
    if is_large and await public_download_service.wait_until_ready(timeout=45):
        web_url = public_download_service.create_web_session(
            "youtube", url, update.effective_user.id,
            title=info.get("title"), uploader=info.get("uploader"), duration=info.get("duration"),
        )
        if web_url:
            keyboard.append([InlineKeyboardButton("🌐 Play / Download Long Video on Website", url=web_url)])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="close_menu")])

    await status_msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def yt_quality_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle YouTube quality selection callback query"""
    query = update.callback_query
    await query.answer("📥 Download request initiated...")

    data = query.data or ""
    parts = data.split("_")
    if len(parts) < 4:
        return

    quality = parts[2]
    url_key = parts[3]
    url = PENDING_YT_URLS.get(url_key)

    if not url:
        await query.message.reply_text("❌ *Download session expired. Please send the YouTube link again!*", parse_mode="Markdown")
        return

    status_msg = await query.message.reply_text(f"⏳ *Downloading YouTube video in {quality.upper()} format... Please wait...*", parse_mode="Markdown")

    result = await downloader_service.download_youtube(url, quality=quality)
    if not result or not os.path.exists(result['filepath']):
        await status_msg.edit_text("❌ *Failed to download YouTube video. The video might be restricted or over Telegram size limits.*", parse_mode="Markdown")
        return

    filepath = result['filepath']
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)

    if os.path.getsize(filepath) > TELEGRAM_UPLOAD_SAFE_BYTES:
        web_markup = await _website_download_markup(filepath, update.effective_user.id, result.get("title"))
        if web_markup:
            await status_msg.edit_text(
                f"✅ *Your {quality.upper()} download is ready.*\n"
                f"📦 *Size:* `{file_size_mb:.1f} MB`\n"
                "Open the website to play, download, or save it to your Telegram cloud.",
                parse_mode="Markdown",
                reply_markup=web_markup,
            )
            return
        direct_markup = await _direct_download_markup(filepath)
        if direct_markup:
            await status_msg.edit_text(
                f"✅ *Your {quality.upper()} download is ready.*\n📦 *Size:* `{file_size_mb:.1f} MB`",
                parse_mode="Markdown",
                reply_markup=direct_markup,
            )
            return

    parts = [filepath]
    if not result['is_audio'] and os.path.getsize(filepath) > TELEGRAM_UPLOAD_SAFE_BYTES:
        await status_msg.edit_text(
            f"✂️ *Long video is {file_size_mb:.1f} MB. Splitting it into playable parts for Telegram upload…*",
            parse_mode="Markdown",
        )
        try:
            parts = await downloader_service.split_video_for_telegram(filepath, TELEGRAM_UPLOAD_SAFE_BYTES)
        except Exception as exc:
            await status_msg.edit_text(f"❌ *Could not prepare long video:* {escape_md(str(exc))}", parse_mode="Markdown")
            try:
                os.remove(filepath)
            except OSError:
                pass
            return

    await status_msg.edit_text(f"📤 *Uploading {len(parts)} video part(s) to Telegram…*", parse_mode="Markdown")
    try:
        for index, part_path in enumerate(parts, start=1):
            part_size_mb = os.path.getsize(part_path) / (1024 * 1024)
            part_caption = (
                f"🎬 *{escape_md(result['title'])}*\n"
                f"⚡ *Quality:* `{quality.upper()}` | 📦 *Part:* `{index}/{len(parts)}` | `{part_size_mb:.1f} MB`\n"
                f"🤖 *Downloaded via @{context.bot.username or 'MusicBot'}*"
            )
            with open(part_path, 'rb') as f:
                if result['is_audio']:
                    await update.effective_chat.send_audio(
                        audio=f,
                        caption=part_caption,
                        title=result['title'],
                        performer=result['uploader'],
                        parse_mode="Markdown",
                        read_timeout=300,
                        write_timeout=300,
                        connect_timeout=30,
                    )
                else:
                    await update.effective_chat.send_video(
                        video=f,
                        caption=part_caption,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup([[get_add_to_group_button("video")]]) if index == len(parts) else None,
                        read_timeout=300,
                        write_timeout=300,
                        connect_timeout=30,
                    )
    except Exception as e:
        await status_msg.edit_text(f"❌ *Telegram upload failed:* {escape_md(str(e))}", parse_mode="Markdown")
    finally:
        for part_path in set(parts + [filepath]):
            if os.path.exists(part_path):
                try:
                    os.remove(part_path)
                except Exception:
                    pass

async def insta_command(update: Update, context: ContextTypes.DEFAULT_TYPE, input_url: str = None):
    """Instagram Reels, IGTV, Photos & Videos Downloader"""
    url = input_url or (context.args[0].strip() if context.args else None)
    if not url and update.message and update.message.reply_to_message:
        url = update.message.reply_to_message.text or ""

    if not url or not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ *Please provide a valid Instagram link!*\nExample: `/insta https://www.instagram.com/reel/example`", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("⏳ *Fetching Instagram Reel / Post media...*", parse_mode="Markdown")

    results = await downloader_service.download_instagram(url)
    if not results:
        await status_msg.edit_text("❌ *Failed to download Instagram post. Make sure the account/post is public!*", parse_mode="Markdown")
        return

    await status_msg.edit_text(f"📤 *Uploading {len(results)} Instagram item(s) to Telegram...*", parse_mode="Markdown")

    for item in results:
        filepath = item['filepath']
        if not os.path.exists(filepath):
            continue
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        item_parts = [filepath]
        website_markup = None
        if os.path.getsize(filepath) > TELEGRAM_UPLOAD_SAFE_BYTES:
            web_markup = await _website_download_markup(filepath, update.effective_user.id, item.get("title", "Instagram media"))
            if web_markup:
                await update.effective_chat.send_message(
                    f"✅ *Instagram media ready*\n📦 *Size:* `{file_size_mb:.1f} MB`",
                    parse_mode="Markdown",
                    reply_markup=web_markup,
                )
                continue
            direct_markup = await _direct_download_markup(filepath)
            if direct_markup:
                await update.effective_chat.send_message(
                    f"✅ *Instagram download ready*\n📦 *Size:* `{file_size_mb:.1f} MB`",
                    parse_mode="Markdown",
                    reply_markup=direct_markup,
                )
                continue
        elif public_download_service.ready:
            website_markup = await _website_download_markup(filepath, update.effective_user.id, item.get("title", "Instagram media"))
        if item['is_video'] and os.path.getsize(filepath) > TELEGRAM_UPLOAD_SAFE_BYTES:
            try:
                item_parts = await downloader_service.split_video_for_telegram(filepath, TELEGRAM_UPLOAD_SAFE_BYTES)
            except Exception as exc:
                await update.effective_chat.send_message(f"❌ Could not prepare large Instagram video: {escape_md(str(exc))}", parse_mode="Markdown")
                try:
                    os.remove(filepath)
                except OSError:
                    pass
                continue

        try:
            for index, part_path in enumerate(item_parts, start=1):
                part_caption = f"📸 *Instagram Video*\n📝 {escape_md(item['title'])}\n📦 *Part:* `{index}/{len(item_parts)}`"
                with open(part_path, 'rb') as f:
                    if item['is_video']:
                        await update.effective_chat.send_video(
                            video=f,
                            caption=part_caption,
                            parse_mode="Markdown",
                            reply_markup=InlineKeyboardMarkup(
                                ([[website_markup.inline_keyboard[0][0]]] if website_markup else [])
                                + [[get_add_to_group_button("video")]]
                            ) if index == len(item_parts) else None,
                            read_timeout=300,
                            write_timeout=300,
                            connect_timeout=30,
                        )
                    else:
                        await update.effective_chat.send_photo(
                            photo=f,
                            caption=part_caption,
                            parse_mode="Markdown",
                            reply_markup=InlineKeyboardMarkup(
                                ([[website_markup.inline_keyboard[0][0]]] if website_markup else [])
                                + [[get_add_to_group_button("photo")]]
                            ),
                        )
        except Exception as e:
            await update.effective_chat.send_message(f"❌ Upload error: {e}")
        finally:
            paths_to_remove = [] if website_markup else item_parts + [filepath]
            for part_path in set(paths_to_remove):
                if not os.path.exists(part_path):
                    continue
                try:
                    os.remove(part_path)
                except Exception:
                    pass

async def github_command(update: Update, context: ContextTypes.DEFAULT_TYPE, input_url: str = None):
    """GitHub Source Code Downloader (Downloads ZIP Archive, Releases, or Files)"""
    url = input_url or (context.args[0].strip() if context.args else None)
    if not url and update.message and update.message.reply_to_message:
        url = update.message.reply_to_message.text or ""

    if not url or ("github.com" not in url and "raw.githubusercontent.com" not in url):
        await update.message.reply_text("❌ *Please provide a valid GitHub repository, release, or file URL!*\nExample: `/github https://github.com/torvalds/linux`", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("⏳ *Fetching GitHub repository / file...*", parse_mode="Markdown")

    result = await downloader_service.download_github_repo(url)
    if not result or not os.path.exists(result['filepath']):
        await status_msg.edit_text("❌ *Failed to download from GitHub. Please verify the repository link, branch, or release file!*", parse_mode="Markdown")
        return

    filepath = result['filepath']
    file_size_mb = result['file_size'] / (1024 * 1024)
    website_markup = None

    if result['file_size'] > TELEGRAM_UPLOAD_SAFE_BYTES:
        web_markup = await _website_download_markup(filepath, update.effective_user.id, result.get("filename", "GitHub download"))
        if web_markup:
            await status_msg.edit_text(
                f"✅ *GitHub download is ready.*\n📦 *Size:* `{file_size_mb:.1f} MB`",
                parse_mode="Markdown", reply_markup=web_markup,
            )
            return
        direct_markup = await _direct_download_markup(filepath)
        if direct_markup:
            await status_msg.edit_text(f"✅ *GitHub download is ready.*\n📦 *Size:* `{file_size_mb:.1f} MB`", parse_mode="Markdown", reply_markup=direct_markup)
            return

    if public_download_service.ready and result['file_size'] <= TELEGRAM_UPLOAD_SAFE_BYTES:
        website_markup = await _website_download_markup(filepath, update.effective_user.id, result.get("filename", "GitHub download"))

    if file_size_mb > 49.5:
        if os.path.exists(filepath) and not website_markup:
            try:
                os.remove(filepath)
            except Exception:
                pass
        await status_msg.edit_text(f"⚠️ *GitHub file size ({file_size_mb:.1f} MB) exceeds Telegram standard bot upload limit (50 MB).*", parse_mode="Markdown")
        return

    await status_msg.edit_text("📤 *Uploading GitHub content to Telegram...*", parse_mode="Markdown")

    if result.get('is_single_file'):
        caption = (
            f"📄 *GITHUB FILE DOWNLOAD*\n"
            f"📁 *File Name:* `{escape_md(result['filename'])}`\n"
            f"📊 *Size:* `{file_size_mb:.2f} MB`\n"
            f"🤖 *Downloaded via Telegram Music Bot*"
        )
    else:
        caption = (
            f"📦 *GITHUB SOURCE CODE ZIP*\n"
            f"📁 *Repo:* `{escape_md(result['repo_name'])}`\n"
            f"📊 *Archive Size:* `{file_size_mb:.2f} MB`\n"
            f"🤖 *Downloaded via Telegram Music Bot*"
        )

    try:
        with open(filepath, 'rb') as f:
            await update.effective_chat.send_document(
                document=f,
                filename=result['filename'],
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    ([[website_markup.inline_keyboard[0][0]]] if website_markup else [])
                    + [[get_add_to_group_button("file")]]
                )
            )
    except Exception as e:
        await status_msg.edit_text(f"❌ Upload error: {escape_md(str(e))}", parse_mode="Markdown")
    finally:
        if os.path.exists(filepath) and not website_markup:
            try:
                os.remove(filepath)
            except Exception:
                pass

async def gdrive_command(update: Update, context: ContextTypes.DEFAULT_TYPE, input_url: str = None):
    """Google Drive Photo, Video, Audio, File & Folder Downloader"""
    url = input_url or (context.args[0].strip() if context.args else None)
    if not url and update.message and update.message.reply_to_message:
        url = update.message.reply_to_message.text or ""

    if not url or not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ *Please provide a valid Google Drive shareable link!*\nExample: `/gdrive https://drive.google.com/file/d/.../view`", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("⏳ *Downloading file from Google Drive... Please wait...*", parse_mode="Markdown")

    result = await downloader_service.download_gdrive(url)
    if not result or not os.path.exists(result['filepath']):
        await status_msg.edit_text("❌ *Failed to download Google Drive file. Ensure link sharing is set to 'Anyone with the link' and the file exists!*", parse_mode="Markdown")
        return

    filepath = result['filepath']
    file_size_mb = result['file_size'] / (1024 * 1024)
    website_markup = None

    if result['file_size'] > TELEGRAM_UPLOAD_SAFE_BYTES:
        web_markup = await _website_download_markup(filepath, update.effective_user.id, result.get("filename", "Google Drive file"))
        if web_markup:
            await status_msg.edit_text(
                f"✅ *Google Drive download is ready.*\n📦 *Size:* `{file_size_mb:.1f} MB`",
                parse_mode="Markdown", reply_markup=web_markup,
            )
            return
        direct_markup = await _direct_download_markup(filepath)
        if direct_markup:
            await status_msg.edit_text(f"✅ *Google Drive download is ready.*\n📦 *Size:* `{file_size_mb:.1f} MB`", parse_mode="Markdown", reply_markup=direct_markup)
            return

    if public_download_service.ready and result['file_size'] <= TELEGRAM_UPLOAD_SAFE_BYTES:
        website_markup = await _website_download_markup(filepath, update.effective_user.id, result.get("filename", "Google Drive file"))

    if file_size_mb > 49.5:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
        await status_msg.edit_text(f"⚠️ *Drive file size ({file_size_mb:.1f} MB) exceeds Telegram standard bot upload limit (50 MB).*", parse_mode="Markdown")
        return

    await status_msg.edit_text("📤 *Uploading Google Drive file to Telegram...*", parse_mode="Markdown")

    caption = (
        f"📁 *GOOGLE DRIVE FILE*\n"
        f"📄 *File Name:* `{escape_md(result['filename'])}`\n"
        f"📊 *File Size:* `{file_size_mb:.2f} MB`\n"
        f"🤖 *Downloaded via Telegram Music Bot*"
    )

    try:
        with open(filepath, 'rb') as f:
            if result.get('is_video'):
                await update.effective_chat.send_video(
                    video=f,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(
                        ([[website_markup.inline_keyboard[0][0]]] if website_markup else [])
                        + [[get_add_to_group_button("video")]]
                    )
                )
            elif result.get('is_audio'):
                await update.effective_chat.send_audio(
                    audio=f,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(
                        ([[website_markup.inline_keyboard[0][0]]] if website_markup else [])
                        + [[get_add_to_group_button("music")]]
                    )
                )
            elif result.get('is_photo'):
                await update.effective_chat.send_photo(
                    photo=f,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(
                        ([[website_markup.inline_keyboard[0][0]]] if website_markup else [])
                        + [[get_add_to_group_button("photo")]]
                    )
                )
            else:
                await update.effective_chat.send_document(
                    document=f,
                    filename=result['filename'],
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(
                        ([[website_markup.inline_keyboard[0][0]]] if website_markup else [])
                        + [[get_add_to_group_button("file")]]
                    )
                )
    except Exception as e:
        await status_msg.edit_text(f"❌ Upload error: {escape_md(str(e))}", parse_mode="Markdown")
    finally:
        if os.path.exists(filepath) and not website_markup:
            try:
                os.remove(filepath)
            except Exception:
                pass

async def pinterest_command(update: Update, context: ContextTypes.DEFAULT_TYPE, input_url: str = None):
    """Pinterest Photo, Video, and Music Downloader (/pin <url> or /pinterest <url>)"""
    url = input_url or (context.args[0].strip() if context.args else None)
    if not url and update.message and update.message.reply_to_message:
        url = update.message.reply_to_message.text or ""

    if not url or not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text(
            "❌ *Please provide a valid Pinterest URL!*\n"
            "• Examples:\n"
            "  `/pin https://pin.it/example`\n"
            "  `/pin https://www.pinterest.com/pin/123456/`",
            parse_mode="Markdown"
        )
        return

    status_msg = await update.message.reply_text("🔍 *Analyzing Pinterest content...*", parse_mode="Markdown")

    info = await downloader_service.get_pinterest_info(url)
    if not info:
        # Fallback: attempt direct photo download
        info = {'title': 'Pinterest Media', 'is_video': False}

    canonical_url = info.get('canonical_url') or url
    url_key = str(abs(hash(canonical_url)))[:10]
    PENDING_PIN_URLS[url_key] = canonical_url

    # If it's a Video pin: offer Video (MP4) and Audio/Music (MP3) download
    if info.get('is_video'):
        title = escape_md(info.get('title') or "Pinterest Video")
        text = (
            f"📌 *PINTEREST VIDEO & MUSIC DOWNLOADER* ⚡\n\n"
            f"📝 *Title:* {title}\n"
            f"👤 *Creator:* {escape_md(info.get('uploader') or 'Pinterest')}\n\n"
            f"👇 *Choose download format:*🔻"
        )
        keyboard = [
            [
                InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"pin_dl_video_{url_key}"),
                InlineKeyboardButton("🎵 Music / Audio (MP3)", callback_data=f"pin_dl_audio_{url_key}")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="close_menu")
            ]
        ]
        await status_msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # If it's a Photo pin: download and send immediately
    await status_msg.edit_text("⏳ *Downloading high-resolution Pinterest photo...*", parse_mode="Markdown")

    result = await downloader_service.download_pinterest(canonical_url, media_type="photo")
    if not result or not os.path.exists(result['filepath']):
        await status_msg.edit_text("❌ *Failed to download Pinterest photo. Ensure the pin is public and accessible!*", parse_mode="Markdown")
        return

    filepath = result['filepath']
    file_size_mb = result['file_size'] / (1024 * 1024)

    website_markup = None
    if public_download_service.ready:
        website_markup = await _website_download_markup(filepath, update.effective_user.id, result.get("title", "Pinterest photo"))

    await status_msg.edit_text("📤 *Uploading photo to Telegram...*", parse_mode="Markdown")

    caption = (
        f"📸 *PINTEREST PHOTO*\n"
        f"📝 *Title:* {escape_md(result['title'])}\n"
        f"📊 *Size:* `{file_size_mb:.2f} MB`\n"
        f"🤖 *Downloaded via @{context.bot.username or 'MusicBot'}*"
    )

    try:
        with open(filepath, 'rb') as f:
            await update.effective_chat.send_photo(
                photo=f,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    ([[website_markup.inline_keyboard[0][0]]] if website_markup else [])
                    + [[get_add_to_group_button("photo")]]
                )
            )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Upload error: {escape_md(str(e))}", parse_mode="Markdown")
    finally:
        if os.path.exists(filepath) and not website_markup:
            try:
                os.remove(filepath)
            except Exception:
                pass

async def pinterest_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Pinterest Video vs Music/Audio download callback"""
    query = update.callback_query
    await query.answer("📥 Download request initiated...")

    data = query.data or ""
    parts = data.split("_")
    if len(parts) < 4:
        return

    media_type = parts[2]  # "video" or "audio"
    url_key = parts[3]
    url = PENDING_PIN_URLS.get(url_key)

    if not url:
        await query.message.reply_text("❌ *Download session expired. Please send the Pinterest link again!*", parse_mode="Markdown")
        return

    label = "Music / Audio (MP3)" if media_type == "audio" else "Video (MP4)"
    status_msg = await query.message.reply_text(f"⏳ *Downloading Pinterest {label}... Please wait...*", parse_mode="Markdown")

    result = await downloader_service.download_pinterest(url, media_type=media_type)
    if not result or not os.path.exists(result['filepath']):
        await status_msg.edit_text(f"❌ *Failed to download Pinterest {label}. The media may be restricted or unavailable.*", parse_mode="Markdown")
        return

    filepath = result['filepath']
    file_size_mb = result['file_size'] / (1024 * 1024)

    if result['file_size'] > TELEGRAM_UPLOAD_SAFE_BYTES:
        web_markup = await _website_download_markup(filepath, update.effective_user.id, result.get("title", "Pinterest media"))
        if web_markup:
            await status_msg.edit_text(
                f"✅ *Pinterest {escape_md(label)} is ready.*\n📦 *Size:* `{file_size_mb:.1f} MB`",
                parse_mode="Markdown", reply_markup=web_markup,
            )
            return
        direct_markup = await _direct_download_markup(filepath)
        if direct_markup:
            await status_msg.edit_text(f"✅ *Pinterest {escape_md(label)} is ready.*\n📦 *Size:* `{file_size_mb:.1f} MB`", parse_mode="Markdown", reply_markup=direct_markup)
            return

    if file_size_mb > 49.5:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
        await status_msg.edit_text(f"⚠️ *File size ({file_size_mb:.1f} MB) exceeds Telegram standard bot upload limit (50 MB).*", parse_mode="Markdown")
        return

    await status_msg.edit_text(f"📤 *Uploading {label} to Telegram...*", parse_mode="Markdown")

    caption = (
        f"{'🎵' if media_type == 'audio' else '🎬'} *PINTEREST {escape_md(label.upper())}*\n"
        f"📝 *Title:* {escape_md(result['title'])}\n"
        f"📊 *Size:* `{file_size_mb:.2f} MB`\n"
        f"🤖 *Downloaded via @{context.bot.username or 'MusicBot'}*"
    )

    try:
        with open(filepath, 'rb') as f:
            if media_type == "audio":
                await update.effective_chat.send_audio(
                    audio=f,
                    caption=caption,
                    title=result['title'],
                    performer=result.get('uploader') or "Pinterest",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[get_add_to_group_button("music")]])
                )
            else:
                await update.effective_chat.send_video(
                    video=f,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[get_add_to_group_button("video")]])
                )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Upload error: {escape_md(str(e))}", parse_mode="Markdown")
    finally:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
