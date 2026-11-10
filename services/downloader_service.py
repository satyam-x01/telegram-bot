import asyncio
import os
import re
import sys
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Dict, List, Optional
import requests
import yt_dlp
from urllib.parse import urlparse, unquote

try:
    import gdown
except Exception:
    gdown = None

# Ensure parent directory is in sys.path when script is executed directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DOWNLOAD_DIR

class DownloaderService:
    def __init__(self):
        self.download_dir = DOWNLOAD_DIR
        os.makedirs(self.download_dir, exist_ok=True)

    @staticmethod
    def prepare_large_video_support():
        """Check FFmpeg availability when starting the bot directly with bot.py."""
        if shutil.which("ffmpeg") and shutil.which("ffprobe"):
            return "FFmpeg and ffprobe are ready."

        # Termux packages must be installed through its native package manager.
        if os.path.isdir("/data/data/com.termux"):
            pkg = shutil.which("pkg")
            if not pkg:
                raise RuntimeError("Termux package manager `pkg` was not found.")
            subprocess.run([pkg, "install", "-y", "ffmpeg"], check=True, timeout=300)
            if shutil.which("ffmpeg") and shutil.which("ffprobe"):
                return "FFmpeg installed and ready."
            raise RuntimeError("FFmpeg installation completed, but ffmpeg/ffprobe are still unavailable.")

        # Windows uses static-ffmpeg, which fetches its binaries on first split.
        if os.name == "nt":
            try:
                import static_ffmpeg.run  # noqa: F401
                return "FFmpeg helper is ready; binaries will be fetched if needed."
            except ImportError:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "static-ffmpeg>=3.0"],
                    check=True,
                    timeout=300,
                )
                return "FFmpeg helper installed; binaries will be fetched if needed."

        return "FFmpeg not found; large-video splitting may be unavailable."

    async def get_yt_info(self, url: str) -> Optional[Dict]:
        """Fetch YouTube video info without downloading."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_yt_info_sync, url)

    def _get_yt_info_sync(self, url: str) -> Optional[Dict]:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and 'entries' in info and len(info['entries']) > 0:
                    info = info['entries'][0]

                if not info:
                    return None

                estimated_sizes = [
                    fmt.get('filesize') or fmt.get('filesize_approx') or 0
                    for fmt in (info.get('formats') or [])
                    if fmt.get('vcodec') not in (None, 'none')
                ]

                return {
                    'title': info.get('title', 'YouTube Video'),
                    'duration': info.get('duration', 0),
                    'estimated_size': max(estimated_sizes, default=0),
                    'uploader': info.get('uploader', 'Channel'),
                    'thumbnail': info.get('thumbnail'),
                    'video_id': info.get('id'),
                    'url': url
                }
        except Exception as e:
            print(f"Error fetching YT info: {e}")
            return None

    async def download_youtube(self, url: str, quality: str = "720") -> Optional[Dict]:
        """Download YouTube video/shorts/audio in requested quality."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_youtube_sync, url, quality)

    async def split_video_for_telegram(self, filepath: str, max_part_bytes: int = 45 * 1024 * 1024) -> List[str]:
        """Split a large MP4 into playable parts below Telegram's cloud upload cap."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._split_video_for_telegram_sync, filepath, max_part_bytes)

    @staticmethod
    def _get_ffmpeg_tools():
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        if ffmpeg and ffprobe:
            return ffmpeg, ffprobe

        # On Windows, static-ffmpeg can fetch a platform build on first use.
        # Resolve its absolute executable paths directly instead of assuming
        # its optional PATH setup succeeded during module import.
        try:
            from static_ffmpeg.run import get_or_fetch_platform_executables_else_raise
            ffmpeg, ffprobe = get_or_fetch_platform_executables_else_raise()
            if os.path.isfile(ffmpeg) and os.path.isfile(ffprobe):
                return ffmpeg, ffprobe
        except Exception as exc:
            raise RuntimeError(
                "FFmpeg/ffprobe is required for large videos. On Termux run `pkg install ffmpeg`; "
                "on Windows install FFmpeg or install project requirements and retry."
            ) from exc
        raise RuntimeError(
            "FFmpeg/ffprobe is required for large videos. On Termux run `pkg install ffmpeg`; "
            "on Windows install FFmpeg or install project requirements and retry."
        )

    def _split_video_for_telegram_sync(self, filepath: str, max_part_bytes: int) -> List[str]:
        if not os.path.isfile(filepath):
            raise FileNotFoundError("Downloaded video was not found")
        ffmpeg, ffprobe = self._get_ffmpeg_tools()

        try:
            probe = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filepath],
                capture_output=True, text=True, timeout=30, check=True,
            )
            duration = float(probe.stdout.strip())
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise RuntimeError("Could not read video duration. Ensure FFmpeg and ffprobe are installed.") from exc
        if duration <= 0:
            raise RuntimeError("Video duration is unavailable; cannot safely split it")

        original_size = os.path.getsize(filepath)
        # Start conservatively, then reduce segment time if keyframe alignment
        # or container overhead leaves any part above the safe Telegram size.
        segment_seconds = max(5, duration * (max_part_bytes / original_size) * 0.82)
        output_pattern = str(Path(filepath).with_name(Path(filepath).stem + f"_{uuid.uuid4().hex[:8]}_part_%03d.mp4"))
        for attempt in range(7):
            for previous in self.download_dir.glob(Path(output_pattern).name.replace("%03d", "*")):
                try:
                    previous.unlink()
                except OSError:
                    pass
            command = [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", filepath,
                "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", "-f", "segment", "-segment_time", f"{segment_seconds:.3f}",
                "-reset_timestamps", "1", "-segment_format", "mp4", "-segment_format_options", "movflags=+faststart",
                output_pattern,
            ]
            try:
                subprocess.run(command, capture_output=True, text=True, timeout=max(180, int(duration * 2)), check=True)
            except (OSError, subprocess.SubprocessError) as exc:
                detail = getattr(exc, "stderr", "") or str(exc)
                raise RuntimeError(f"FFmpeg could not split this video: {detail[-500:]}") from exc

            parts = sorted(self.download_dir.glob(Path(output_pattern).name.replace("%03d", "*")))
            if parts and all(part.stat().st_size <= max_part_bytes for part in parts):
                return [str(part) for part in parts]
            for part in parts:
                try:
                    part.unlink()
                except OSError:
                    pass
            segment_seconds *= 0.65

        raise RuntimeError("Could not split the video below Telegram's upload size limit. Try a lower video quality.")

    def _download_youtube_sync(self, url: str, quality: str) -> Optional[Dict]:
        out_template = str(self.download_dir / f"%(id)s_{quality}.%(ext)s")

        if quality == "mp3":
            format_spec = 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best'
        elif quality == "1080":
            format_spec = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
        elif quality == "720":
            format_spec = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
        elif quality == "480":
            format_spec = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
        elif quality == "360":
            format_spec = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best'
        else:
            format_spec = 'best[ext=mp4]/best'

        ydl_opts = {
            'format': format_spec,
            'outtmpl': out_template,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'continuedl': True,
            'retries': 10,
            'fragment_retries': 10,
            'file_access_retries': 5,
            'socket_timeout': 30,
            'merge_output_format': 'mp4' if quality != "mp3" else None,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info and 'entries' in info and len(info['entries']) > 0:
                    info = info['entries'][0]

                if not info:
                    return None

                filepath = ydl.prepare_filename(info)
                if quality != "mp3" and not filepath.endswith(".mp4"):
                    base_path = os.path.splitext(filepath)[0] + ".mp4"
                    if os.path.exists(base_path):
                        filepath = base_path

                video_id = info.get('id')
                if not os.path.exists(filepath) and video_id:
                    for f in os.listdir(self.download_dir):
                        if video_id in f and quality in f:
                            filepath = str(self.download_dir / f)
                            break

                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    return {
                        'filepath': filepath,
                        'title': info.get('title', 'YouTube Downloader'),
                        'uploader': info.get('uploader', 'YouTube'),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail'),
                        'quality': quality,
                        'file_size': os.path.getsize(filepath),
                        'is_audio': quality == "mp3"
                    }
        except Exception as e:
            print(f"Error downloading YouTube URL '{url}' ({quality}): {e}")
        return None

    async def download_instagram(self, url: str) -> Optional[List[Dict]]:
        """Download Instagram Reels, IGTV, Photos, or Posts."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_instagram_sync, url)

    def _download_instagram_sync(self, url: str) -> Optional[List[Dict]]:
        out_template = str(self.download_dir / "insta_%(id)s_%(autonumber)s.%(ext)s")
        ydl_opts = {
            'outtmpl': out_template,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
        }
        results = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    return None

                entries = info.get('entries', [info])
                title = info.get('title') or info.get('description') or "Instagram Downloader"
                if len(title) > 100:
                    title = title[:97] + "..."

                for entry in entries:
                    if not entry:
                        continue
                    filename = ydl.prepare_filename(entry)
                    if not os.path.exists(filename):
                        eid = entry.get('id')
                        if eid:
                            for f in os.listdir(self.download_dir):
                                if eid in f and f.startswith("insta_"):
                                    filename = str(self.download_dir / f)
                                    break

                    if os.path.exists(filename) and os.path.getsize(filename) > 0:
                        ext = os.path.splitext(filename)[1].lower()
                        is_video = ext in ['.mp4', '.mkv', '.webm', '.mov']
                        results.append({
                            'filepath': filename,
                            'title': title,
                            'is_video': is_video,
                            'file_size': os.path.getsize(filename)
                        })
        except Exception as e:
            print(f"Error downloading Instagram '{url}': {e}")
        return results if results else None

    async def download_github_repo(self, repo_url: str) -> Optional[Dict]:
        """Download GitHub repository source code as a ZIP archive, release asset, or single file."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_github_repo_sync, repo_url)

    def _download_github_repo_sync(self, repo_url: str) -> Optional[Dict]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        # 1. Check if direct GitHub release download (e.g., releases/download/v1.0/app.zip or .apk)
        if "github.com" in repo_url and "/releases/download/" in repo_url:
            try:
                resp = requests.get(repo_url, stream=True, timeout=60, headers=headers, allow_redirects=True)
                if resp.status_code == 200:
                    filename = os.path.basename(urlparse(resp.url).path) or "github_release_file"
                    out_path = str(self.download_dir / filename)
                    with open(out_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=16384):
                            if chunk:
                                f.write(chunk)
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                        return {
                            'filepath': out_path,
                            'filename': filename,
                            'repo_name': "GitHub Release Asset",
                            'file_size': os.path.getsize(out_path),
                            'is_single_file': True
                        }
            except Exception as e:
                print(f"GitHub release asset download failed: {e}")

        # 2. Check if GitHub raw file or blob URL
        raw_match = re.search(r"github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)", repo_url)
        if raw_match:
            user, repo, branch, filepath_in_repo = raw_match.group(1), raw_match.group(2), raw_match.group(3), raw_match.group(4)
            raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{filepath_in_repo}"
            try:
                resp = requests.get(raw_url, stream=True, timeout=30, headers=headers)
                if resp.status_code == 200:
                    fname = os.path.basename(filepath_in_repo) or "github_file"
                    out_path = str(self.download_dir / fname)
                    with open(out_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=16384):
                            if chunk:
                                f.write(chunk)
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                        return {
                            'filepath': out_path,
                            'filename': fname,
                            'repo_name': f"{user}/{repo}",
                            'file_size': os.path.getsize(out_path),
                            'is_single_file': True
                        }
            except Exception as e:
                print(f"GitHub blob raw download failed: {e}")

        # 3. Check if raw.githubusercontent.com direct URL
        if "raw.githubusercontent.com" in repo_url:
            try:
                resp = requests.get(repo_url, stream=True, timeout=30, headers=headers)
                if resp.status_code == 200:
                    fname = os.path.basename(urlparse(repo_url).path) or "github_raw_file"
                    out_path = str(self.download_dir / fname)
                    with open(out_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=16384):
                            if chunk:
                                f.write(chunk)
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                        return {
                            'filepath': out_path,
                            'filename': fname,
                            'repo_name': "GitHub Raw",
                            'file_size': os.path.getsize(out_path),
                            'is_single_file': True
                        }
            except Exception as e:
                print(f"raw.githubusercontent.com download failed: {e}")

        # 4. Standard Repository Source Code ZIP Download
        match = re.search(r"github\.com/([^/]+)/([^/#?]+)", repo_url)
        if not match:
            return None

        user = match.group(1).strip()
        repo = match.group(2).strip().replace(".git", "")

        # Extract specific branch if specified in /tree/<branch>
        branch_match = re.search(r"github\.com/[^/]+/[^/]+/tree/([^/#?]+)", repo_url)
        branch = branch_match.group(1).strip() if branch_match else None

        zip_urls = []
        if branch:
            zip_urls.extend([
                f"https://github.com/{user}/{repo}/archive/refs/heads/{branch}.zip",
                f"https://codeload.github.com/{user}/{repo}/zip/refs/heads/{branch}"
            ])

        zip_urls.extend([
            f"https://github.com/{user}/{repo}/archive/HEAD.zip",
            f"https://codeload.github.com/{user}/{repo}/zip/refs/heads/main",
            f"https://codeload.github.com/{user}/{repo}/zip/refs/heads/master",
            f"https://api.github.com/repos/{user}/{repo}/zipball"
        ])

        out_zip = str(self.download_dir / f"{user}_{repo}_{branch or 'main'}_source.zip")

        for zip_url in zip_urls:
            try:
                resp = requests.get(zip_url, stream=True, timeout=40, headers=headers, allow_redirects=True)
                if resp.status_code == 200:
                    with open(out_zip, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=16384):
                            if chunk:
                                f.write(chunk)

                    # Validate valid ZIP magic bytes: PK\x03\x04
                    if os.path.exists(out_zip) and os.path.getsize(out_zip) > 100:
                        with open(out_zip, 'rb') as f:
                            magic = f.read(4)
                        if magic.startswith(b'PK'):
                            return {
                                'filepath': out_zip,
                                'filename': f"{repo}-source-code.zip",
                                'repo_name': f"{user}/{repo}",
                                'file_size': os.path.getsize(out_zip),
                                'is_single_file': False
                            }
                        else:
                            # Not a real zip (e.g. error HTML page), clean up and try next
                            try:
                                os.remove(out_zip)
                            except Exception:
                                pass
            except Exception as e:
                print(f"GitHub ZIP download attempt failed for {zip_url}: {e}")

        return None

    async def download_gdrive(self, drive_url: str) -> Optional[Dict]:
        """Download Google Drive file, video, music, photo, or document."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_gdrive_sync, drive_url)

    def _download_gdrive_sync(self, drive_url: str) -> Optional[Dict]:
        file_id_match = re.search(r"(?:file/d/|id=|folders/|d/|uc\?id=)([a-zA-Z0-9_-]{25,})", drive_url)
        file_id = file_id_match.group(1) if file_id_match else None

        # Strategy 1: gdown (handles virus scan confirmations & new Google Drive endpoints)
        if gdown:
            try:
                dest = str(self.download_dir) + os.sep
                out_path = gdown.download(url=drive_url, output=dest, quiet=True, fuzzy=True)
                if not out_path and file_id:
                    out_path = gdown.download(id=file_id, output=dest, quiet=True)
                if out_path and os.path.exists(out_path) and os.path.getsize(out_path) > 100:
                    res = self._build_gdrive_result(out_path)
                    if res:
                        return res
            except Exception as e:
                print(f"gdown download failed for '{drive_url}': {e}")

        # Strategy 2: yt-dlp (works well for videos & audio hosted on Google Drive)
        try:
            out_template = str(self.download_dir / "gdrive_%(id)s_%(title)s.%(ext)s")
            ydl_opts = {
                'outtmpl': out_template,
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(drive_url, download=True)
                if info:
                    filepath = ydl.prepare_filename(info)
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
                        res = self._build_gdrive_result(filepath)
                        if res:
                            return res
        except Exception as e:
            print(f"yt-dlp GDrive fallback failed: {e}")

        # Strategy 3: Direct download from drive.usercontent.google.com with confirmation form parsing
        if file_id:
            try:
                session = requests.Session()
                session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
                resp = session.get(download_url, stream=True, timeout=40)

                # Check if confirmation form exists (large files)
                if "download-form" in resp.text:
                    action_match = re.search(r'action="([^"]+)"', resp.text)
                    if action_match:
                        form_url = action_match.group(1).replace("&amp;", "&")
                        resp = session.get(form_url, stream=True, timeout=40)

                # Check content disposition for original filename
                filename = f"gdrive_file_{file_id[:8]}"
                cd = resp.headers.get('content-disposition', '')
                if 'filename=' in cd:
                    fname_match = re.findall(r'filename="?([^";]+)"?', cd)
                    if fname_match:
                        filename = fname_match[0]

                out_filepath = str(self.download_dir / filename)
                with open(out_filepath, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk)

                if os.path.exists(out_filepath) and os.path.getsize(out_filepath) > 100:
                    res = self._build_gdrive_result(out_filepath)
                    if res:
                        return res
            except Exception as e:
                print(f"Direct GDrive stream fallback failed: {e}")

        return None

    def _build_gdrive_result(self, filepath: str) -> Optional[Dict]:
        """Inspect downloaded GDrive file and construct metadata result dictionary."""
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return None

        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        is_video = ext in ['.mp4', '.mkv', '.webm', '.mov', '.avi']
        is_audio = ext in ['.mp3', '.m4a', '.wav', '.flac', '.ogg', '.aac']
        is_photo = ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']

        return {
            'filepath': filepath,
            'filename': filename,
            'file_size': os.path.getsize(filepath),
            'is_video': is_video,
            'is_audio': is_audio,
            'is_photo': is_photo
        }

    async def get_pinterest_info(self, url: str) -> Optional[Dict]:
        """Fetch Pinterest pin information and determine whether it's a Video or Photo."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_pinterest_info_sync, url)

    def _get_pinterest_info_sync(self, url: str) -> Optional[Dict]:
        canonical_url = self._resolve_pinterest_url(url)
        if not canonical_url:
            canonical_url = url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        # First check with yt-dlp for video metadata
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(canonical_url, download=False)
                if info and (info.get('formats') or info.get('url')):
                    title = info.get('title') or info.get('description') or "Pinterest Video"
                    if len(title) > 80:
                        title = title[:77] + "..."
                    return {
                        'title': title,
                        'is_video': True,
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail'),
                        'uploader': info.get('uploader') or "Pinterest Creator",
                        'canonical_url': canonical_url
                    }
        except Exception:
            pass

        # If not video or yt-dlp didn't detect video, fetch webpage to extract photo/video metadata
        try:
            resp = requests.get(canonical_url, headers=headers, timeout=15)
            if resp.status_code == 200:
                html = resp.text

                # Check if video tag or og:video is present
                video_match = re.search(r'<meta\s+property="og:video(?::secure_url)?"\s+content="([^"]+)"', html)
                if not video_match:
                    video_match = re.search(r'"(https://v1\.pinimg\.com/videos/[^"]+\.mp4)"', html)

                # Check for og:image or high-res pin image
                img_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
                if not img_match:
                    img_match = re.search(r'"(https://i\.pinimg\.com/(?:originals|[0-9]+x)/[^"]+)"', html)

                # Check for title
                title_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
                title = title_match.group(1) if title_match else "Pinterest Pin"
                if len(title) > 80:
                    title = title[:77] + "..."

                if video_match:
                    return {
                        'title': title,
                        'is_video': True,
                        'video_url': video_match.group(1),
                        'thumbnail': img_match.group(1) if img_match else None,
                        'canonical_url': canonical_url
                    }
                elif img_match:
                    img_url = img_match.group(1)
                    # Convert to original resolution
                    orig_img_url = re.sub(r'/[0-9]+x/', '/originals/', img_url)
                    return {
                        'title': title,
                        'is_video': False,
                        'image_url': orig_img_url,
                        'canonical_url': canonical_url
                    }
        except Exception as e:
            print(f"Error fetching Pinterest pin page: {e}")

        return None

    def _resolve_pinterest_url(self, url: str) -> Optional[str]:
        """Resolve shortened pin.it URLs to full Pinterest canonical URL."""
        if "pin.it" in url:
            try:
                resp = requests.head(url, allow_redirects=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                return resp.url
            except Exception:
                try:
                    resp = requests.get(url, allow_redirects=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    return resp.url
                except Exception:
                    pass
        return url

    async def download_pinterest(self, url: str, media_type: str = "video") -> Optional[Dict]:
        """
        Download Pinterest content:
        - media_type="video": Download MP4 video
        - media_type="audio": Download & extract MP3 audio / music
        - media_type="photo": Download high-resolution photo
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_pinterest_sync, url, media_type)

    def _download_pinterest_sync(self, url: str, media_type: str = "video") -> Optional[Dict]:
        canonical_url = self._resolve_pinterest_url(url) or url

        # 1. Download Photo
        if media_type == "photo":
            info = self._get_pinterest_info_sync(canonical_url)
            img_url = info.get('image_url') if info else None

            if not img_url:
                # Direct page scrape for image
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                try:
                    r = requests.get(canonical_url, headers=headers, timeout=15)
                    match = re.search(r'"(https://i\.pinimg\.com/(?:originals|[0-9]+x)/[^"]+)"', r.text)
                    if match:
                        img_url = re.sub(r'/[0-9]+x/', '/originals/', match.group(1))
                except Exception:
                    pass

            if img_url:
                try:
                    resp = requests.get(img_url, stream=True, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        ext = os.path.splitext(urlparse(img_url).path)[1].lower() or ".jpg"
                        pin_id = re.search(r"([0-9a-zA-Z_-]+)\.(?:jpg|png|webp|jpeg)", img_url)
                        fname = f"pin_{pin_id.group(1) if pin_id else 'photo'}{ext}"
                        out_path = str(self.download_dir / fname)
                        with open(out_path, 'wb') as f:
                            for chunk in resp.iter_content(chunk_size=16384):
                                if chunk:
                                    f.write(chunk)
                        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                            return {
                                'filepath': out_path,
                                'title': (info.get('title') if info else None) or "Pinterest Photo",
                                'is_photo': True,
                                'is_video': False,
                                'is_audio': False,
                                'file_size': os.path.getsize(out_path)
                            }
                except Exception as e:
                    print(f"Error downloading Pinterest photo: {e}")

        # 2. Download Audio / Music from Pinterest Video
        elif media_type == "audio":
            out_template = str(self.download_dir / "pin_audio_%(id)s.%(ext)s")
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': out_template,
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(canonical_url, download=True)
                    if info:
                        filepath = ydl.prepare_filename(info)
                        base_mp3 = os.path.splitext(filepath)[0] + ".mp3"
                        if os.path.exists(base_mp3):
                            filepath = base_mp3

                        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                            title = info.get('title') or "Pinterest Music"
                            return {
                                'filepath': filepath,
                                'title': title,
                                'uploader': info.get('uploader') or "Pinterest",
                                'is_audio': True,
                                'is_video': False,
                                'is_photo': False,
                                'file_size': os.path.getsize(filepath)
                            }
            except Exception as e:
                print(f"yt-dlp Pinterest audio download failed: {e}")

        # 3. Download Video
        else:
            out_template = str(self.download_dir / "pin_video_%(id)s.%(ext)s")
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': out_template,
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'merge_output_format': 'mp4'
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(canonical_url, download=True)
                    if info:
                        filepath = ydl.prepare_filename(info)
                        if not filepath.endswith(".mp4"):
                            base_mp4 = os.path.splitext(filepath)[0] + ".mp4"
                            if os.path.exists(base_mp4):
                                filepath = base_mp4

                        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                            title = info.get('title') or "Pinterest Video"
                            return {
                                'filepath': filepath,
                                'title': title,
                                'uploader': info.get('uploader') or "Pinterest",
                                'is_video': True,
                                'is_audio': False,
                                'is_photo': False,
                                'file_size': os.path.getsize(filepath)
                            }
            except Exception as e:
                print(f"yt-dlp Pinterest video download failed: {e}")

            # Fallback direct video URL download
            info = self._get_pinterest_info_sync(canonical_url)
            video_url = info.get('video_url') if info else None
            if video_url:
                try:
                    resp = requests.get(video_url, stream=True, timeout=40, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        out_path = str(self.download_dir / "pin_video_direct.mp4")
                        with open(out_path, 'wb') as f:
                            for chunk in resp.iter_content(chunk_size=16384):
                                if chunk:
                                    f.write(chunk)
                        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                            return {
                                'filepath': out_path,
                                'title': (info.get('title') if info else None) or "Pinterest Video",
                                'is_video': True,
                                'is_audio': False,
                                'is_photo': False,
                                'file_size': os.path.getsize(out_path)
                            }
                except Exception as e:
                    print(f"Direct Pinterest video download failed: {e}")

        return None

downloader_service = DownloaderService()
