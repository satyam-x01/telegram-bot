import os
import re
import time
import glob
import logging
import threading
from typing import Optional, Dict, Any
from pathlib import Path

import yt_dlp
import urllib.parse
from modules.config import DOWNLOADS_DIR, BIN_DIR, config_manager, logger, get_server_url

class MediaDownloader:
    """Handles downloading YouTube and Instagram videos, format extraction, on-demand streaming, and 24h auto-cleanup."""

    def __init__(self):
        self._info_cache: Dict[str, Any] = {}
        self._download_locks: Dict[str, threading.Lock] = {}
        self._master_lock = threading.Lock()
        self._start_cleanup_worker()

    def get_watch_url(self, url: str) -> str:
        """Generate the web portal watch/download link for a given video URL."""
        base = get_server_url()
        encoded = urllib.parse.quote(url.strip())
        return f"{base}/watch?url={encoded}"

    @staticmethod
    def extract_video_url(text: str) -> Optional[str]:
        """Detect YouTube or Instagram video link in text."""
        # YouTube regex
        yt_regex = r"(https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)[a-zA-Z0-9_\-]+(?:\?[a-zA-Z0-9_=&-]+)?)"
        yt_match = re.search(yt_regex, text)
        if yt_match:
            return yt_match.group(0)

        # Instagram regex
        insta_regex = r"(https?://(?:www\.)?instagram\.com/(?:reel|p|tv)/[a-zA-Z0-9_\-]+/?(?:\?[a-zA-Z0-9_=&-]+)?)"
        insta_match = re.search(insta_regex, text)
        if insta_match:
            return insta_match.group(0)

        return None

    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract metadata, thumbnail, duration, and available formats without full download."""
        clean_url = url.strip()
        if clean_url in self._info_cache:
            return self._info_cache[clean_url]

        try:
            ydl_opts = {
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
                if not info:
                    return None

                vid_id = info.get("id", "video")
                title = info.get("title", "Video")
                thumbnail = info.get("thumbnail", "")
                duration_sec = info.get("duration", 0)
                uploader = info.get("uploader", "") or info.get("channel", "Unknown Creator")

                # Format duration
                if duration_sec:
                    mins = int(duration_sec) // 60
                    secs = int(duration_sec) % 60
                    if mins >= 60:
                        hrs = mins // 60
                        mins = mins % 60
                        duration_str = f"{hrs}:{mins:02d}:{secs:02d}"
                    else:
                        duration_str = f"{mins}:{secs:02d}"
                else:
                    duration_str = "Live / Clip"

                platform = "YouTube" if ("youtube.com" in clean_url or "youtu.be" in clean_url) else "Instagram"

                # Check available formats
                raw_formats = info.get("formats", [])
                available_heights = set()
                for f in raw_formats:
                    h = f.get("height")
                    if h and isinstance(h, int) and f.get("vcodec") != "none":
                        available_heights.add(h)

                # Build quality list
                supported_resolutions = [
                    (1080, "1080p Full HD", "1080p", "High Quality"),
                    (720, "720p HD", "720p", "Recommended"),
                    (480, "480p SD", "480p", "Standard"),
                    (360, "360p Data Saver", "360p", "Fast")
                ]

                formats_list = []
                # If specific heights detected
                if available_heights:
                    for h_val, label, q_key, desc in supported_resolutions:
                        # If available or if close
                        if any(h >= h_val * 0.9 for h in available_heights):
                            formats_list.append({
                                "quality": q_key,
                                "label": label,
                                "ext": "mp4",
                                "desc": desc,
                                "height": h_val
                            })
                else:
                    # Default formats for Instagram / reels
                    formats_list.append({"quality": "best", "label": "Best Quality HD", "ext": "mp4", "desc": "Original", "height": 720})

                if not formats_list:
                    formats_list.append({"quality": "720p", "label": "720p HD", "ext": "mp4", "desc": "Standard", "height": 720})

                # Always add audio option
                formats_list.append({
                    "quality": "audio",
                    "label": "MP3 Audio (High Quality)",
                    "ext": "mp3",
                    "desc": "Music / Speech",
                    "height": 0
                })

                result = {
                    "id": vid_id,
                    "title": title,
                    "thumbnail": thumbnail,
                    "duration": duration_sec,
                    "duration_str": duration_str,
                    "uploader": uploader,
                    "platform": platform,
                    "url": clean_url,
                    "formats": formats_list,
                    "watch_url": self.get_watch_url(clean_url)
                }

                self._info_cache[clean_url] = result
                return result
        except Exception as e:
            logger.error(f"Failed to extract video info for {url}: {e}")
            return None

    def download_format(self, url: str, quality: str = "720p") -> Optional[Dict[str, Any]]:
        """Download or retrieve specific quality (1080p, 720p, 480p, 360p, audio) with caching."""
        clean_url = url.strip()
        info = self.get_video_info(clean_url)
        vid_id = info.get("id", "video") if info else re.sub(r'[^a-zA-Z0-9_\-]', '', clean_url[-16:])

        clean_quality = quality.lower().strip()
        is_audio = clean_quality in ["audio", "mp3"]

        ext = "mp3" if is_audio else "mp4"
        expected_filename = f"{vid_id}_{clean_quality}.{ext}"
        expected_path = DOWNLOADS_DIR / expected_filename

        # If already downloaded, return cached file!
        if expected_path.exists() and expected_path.stat().st_size > 1024:
            return {
                "path": str(expected_path),
                "filename": expected_filename,
                "title": info.get("title", vid_id) if info else vid_id,
                "size": expected_path.stat().st_size,
                "is_audio": is_audio,
                "content_type": "audio/mpeg" if is_audio else "video/mp4"
            }

        # Prevent duplicate parallel downloads of identical file
        with self._master_lock:
            if expected_filename not in self._download_locks:
                self._download_locks[expected_filename] = threading.Lock()
            dl_lock = self._download_locks[expected_filename]

        with dl_lock:
            # Re-check after acquiring lock
            if expected_path.exists() and expected_path.stat().st_size > 1024:
                return {
                    "path": str(expected_path),
                    "filename": expected_filename,
                    "title": info.get("title", vid_id) if info else vid_id,
                    "size": expected_path.stat().st_size,
                    "is_audio": is_audio,
                    "content_type": "audio/mpeg" if is_audio else "video/mp4"
                }

            import shutil
            ffmpeg_bin = BIN_DIR / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
            ffmpeg_path = str(ffmpeg_bin) if ffmpeg_bin.exists() else shutil.which("ffmpeg")

            out_template = str(DOWNLOADS_DIR / f"{vid_id}_{clean_quality}.%(ext)s")

            ydl_opts: Dict[str, Any] = {
                "outtmpl": out_template,
                "ffmpeg_location": ffmpeg_path if (ffmpeg_path and os.path.exists(ffmpeg_path)) else None,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
            }

            if is_audio:
                ydl_opts["format"] = "bestaudio/best"
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
            else:
                h_target = 720
                if "1080" in clean_quality:
                    h_target = 1080
                elif "720" in clean_quality:
                    h_target = 720
                elif "480" in clean_quality:
                    h_target = 480
                elif "360" in clean_quality:
                    h_target = 360

                ydl_opts["format"] = f"bestvideo[height<={h_target}]+bestaudio/best[height<={h_target}]/best"
                ydl_opts["merge_output_format"] = "mp4"

            try:
                logger.info(f"Downloading format [{clean_quality}] for {clean_url}...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([clean_url])

                # Check if file created
                candidates = glob.glob(str(DOWNLOADS_DIR / f"{vid_id}_{clean_quality}.*"))
                final_file = None
                for c in candidates:
                    if os.path.exists(c) and os.path.getsize(c) > 1024:
                        final_file = c
                        break

                if final_file:
                    file_size = os.path.getsize(final_file)
                    logger.info(f"Downloaded [{clean_quality}]: {final_file} ({file_size / (1024*1024):.2f} MB)")
                    return {
                        "path": final_file,
                        "filename": os.path.basename(final_file),
                        "title": info.get("title", vid_id) if info else vid_id,
                        "size": file_size,
                        "is_audio": is_audio,
                        "content_type": "audio/mpeg" if is_audio else "video/mp4"
                    }
            except Exception as e:
                logger.error(f"Error downloading format {clean_quality} for {clean_url}: {e}")
                return None

        return None

    def download_video(self, url: str) -> Optional[Dict[str, Any]]:
        """Legacy helper for direct small WhatsApp transfers (<65MB)."""
        res = self.download_format(url, quality="360p")
        if res and res.get("size", 0) <= 65 * 1024 * 1024:
            return res
        return None

    def cleanup_old_videos(self):
        """Delete local downloaded video files that are older than retention hours (default: 24h)."""
        retention_hours = config_manager.get("video_retention_hours", 24)
        max_age_seconds = retention_hours * 3600
        current_time = time.time()
        deleted_count = 0

        for file_path in DOWNLOADS_DIR.glob("*"):
            if file_path.is_file():
                try:
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Auto-deleted 24h+ local video: {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")

        if deleted_count > 0:
            logger.info(f"24h Cleanup: Deleted {deleted_count} local video(s) to save disk storage.")

    def _start_cleanup_worker(self):
        """Background thread running cleanup check periodically."""
        def worker():
            while True:
                time.sleep(600) # Check every 10 minutes
                try:
                    self.cleanup_old_videos()
                except Exception as e:
                    logger.error(f"Error in cleanup worker: {e}")

        t = threading.Thread(target=worker, daemon=True, name="VideoCleanerThread")
        t.start()

media_downloader = MediaDownloader()
