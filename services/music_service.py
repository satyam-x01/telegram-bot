import asyncio
import os
import random
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
import yt_dlp

# Ensure parent directory is in sys.path when script is executed directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DOWNLOAD_DIR

class MusicService:
    def __init__(self):
        self.download_dir = DOWNLOAD_DIR

    def search_song(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search YouTube for songs matching query across all languages."""
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'default_search': 'ytsearch',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }
        search_query = f"ytsearch{max_results}:{query}"
        results = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            results.append({
                                'id': entry.get('id'),
                                'title': entry.get('title', 'Unknown Title'),
                                'uploader': entry.get('uploader', 'Unknown Artist'),
                                'duration': entry.get('duration', 0),
                                'url': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
                                'thumbnail': entry.get('thumbnail')
                            })
        except Exception as e:
            print(f"Error searching song '{query}': {e}")
        return results

    def fast_get_video_id(self, query: str) -> Optional[Dict]:
        """Ultra-fast flat search to get video_id and metadata in ~0.3 seconds without downloading."""
        if query.startswith("http://") or query.startswith("https://"):
            return None
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch1',
            'socket_timeout': 5,
            'youtube_include_dash_manifest': False,
            'youtube_include_hls_manifest': False,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if info and 'entries' in info and len(info['entries']) > 0:
                    entry = info['entries'][0]
                    if entry and entry.get('id'):
                        return {
                            'video_id': entry.get('id'),
                            'title': entry.get('title', 'Unknown Title'),
                            'uploader': entry.get('uploader', 'Artist'),
                            'duration': entry.get('duration', 0)
                        }
        except Exception:
            pass
    async def get_direct_audio_info(self, video_url_or_query: str) -> Optional[Dict]:
        """Extract direct audio stream URL and metadata in ~3-5 seconds without downloading."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_url_sync, video_url_or_query)

    def _extract_url_sync(self, query: str) -> Optional[Dict]:
        search_term = query if (query.startswith("http://") or query.startswith("https://")) else f"ytsearch1:{query}"
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch1',
            'youtube_include_dash_manifest': False,
            'youtube_include_hls_manifest': False,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_term, download=False)
                if info and 'entries' in info and len(info['entries']) > 0:
                    info = info['entries'][0]

                if not info or not info.get('url'):
                    return None

                return {
                    'stream_url': info.get('url'),
                    'title': info.get('title', 'Unknown Song'),
                    'artist': info.get('uploader', 'Artist'),
                    'duration': info.get('duration', 0),
                    'video_id': info.get('id')
                }
        except Exception as e:
            print(f"Extract URL sync error: {e}")
        return None

    async def download_audio(self, video_url_or_query: str) -> Optional[Dict]:
        """Download audio file for given query or video URL."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._download_sync, video_url_or_query)

    def _download_sync(self, query: str) -> Optional[Dict]:
        out_template = str(self.download_dir / "%(id)s.%(ext)s")
        ydl_opts = {
            'format': 'ba[ext=m4a]/ba[ext=mp3]/ba[ext=webm]/bestaudio/best',
            'outtmpl': out_template,
            'noplaylist': True,
            'quiet': True,
            'noprogress': True,
            'no_warnings': True,
            'default_search': 'ytsearch1',
            'socket_timeout': 10,
            'retries': 2,
            'fragment_retries': 2,
            'concurrent_fragment_downloads': 5,
            'youtube_include_dash_manifest': False,
            'youtube_include_hls_manifest': False,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }

        search_term = query if (query.startswith("http://") or query.startswith("https://")) else f"ytsearch1:{query}"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_term, download=True)
                if info and 'entries' in info and len(info['entries']) > 0:
                    info = info['entries'][0]

                if not info:
                    return None

                video_id = info.get('id')
                title = info.get('title', 'Unknown Song')
                uploader = info.get('uploader', 'Artist')
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail')
                filepath = ydl.prepare_filename(info)

                # Verify downloaded file existence
                if not os.path.exists(filepath) and video_id:
                    for f in os.listdir(self.download_dir):
                        if video_id in f:
                            filepath = str(self.download_dir / f)
                            break

                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    return {
                        'filepath': filepath,
                        'title': title,
                        'artist': uploader,
                        'duration': duration,
                        'thumbnail': thumbnail,
                        'video_id': video_id
                    }
        except Exception as e:
            print(f"Download sync error for search_term '{search_term}': {e}")

        return None

    async def get_phonk_track(self, subgenre: str = "") -> Optional[Dict]:
        """Fetch random top Phonk track."""
        phonk_queries = [
            "Drift Phonk viral 2026",
            "Brazilian Phonk 2026",
            "Aggressive Phonk playlist",
            "Metamorphosis Phonk",
            "Funk Estranho Phonk",
            "Kordhell Phonk best track",
            "LXST CXNTURY Phonk"
        ]
        if subgenre:
            query = f"{subgenre} Phonk music"
        else:
            query = random.choice(phonk_queries)
        return await self.download_audio(query)

    async def get_beats_track(self, subgenre: str = "") -> Optional[Dict]:
        """Fetch random top Beats track."""
        beats_queries = [
            "Lofi Hip Hop chill beats to relax to",
            "Trap beats instrumental 2026",
            "Cyberpunk synthwave beats",
            "Chillhop aesthetic beats",
            "Smooth jazz lofi beats"
        ]
        if subgenre:
            query = f"{subgenre} beats"
        else:
            query = random.choice(beats_queries)
        return await self.download_audio(query)

music_service = MusicService()
