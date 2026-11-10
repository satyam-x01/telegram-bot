"""Temporary, token-protected HTTPS links for files downloaded by this bot.

The origin only listens on localhost. Cloudflare Quick Tunnel (if installed)
provides the public HTTPS URL; random tokens and expiry limit exposure.
"""

import asyncio
import html
import json
import logging
import mimetypes
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

logger = logging.getLogger(__name__)


_WEB_PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><title>Media Download</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#10131c;color:#f3f5fa;font:16px system-ui,Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:18px}
main{width:min(100%,620px);background:#1b2030;border:1px solid #343b50;border-radius:20px;padding:22px;box-shadow:0 16px 48px #0007}h1{font-size:22px;margin:0 0 8px}#meta,#status{color:#bac3d8;line-height:1.5}video,img{width:100%;max-height:62vh;background:#080a10;border-radius:14px;margin-top:16px}select,button,.action{width:100%;border:0;border-radius:12px;padding:14px;margin-top:12px;font-size:16px;color:#fff;background:#343b52}button,.action{background:#5968e8;font-weight:700;text-align:center;text-decoration:none;cursor:pointer}button:disabled{opacity:.55}#actions{display:grid;gap:2px;margin-top:8px}.hidden{display:none!important}.note{font-size:13px;color:#aab3c8;margin-top:16px}
</style></head><body><main>
<h1 id="title">Preparing your media…</h1><div id="meta"></div><div id="player"></div><div id="controls"></div><div id="status" role="status">Loading…</div><div id="actions"></div>
<p class="note">Only download content you have permission to save. This temporary page/link expires when the session ends.</p>
</main><script>
const token=__SESSION__,api=`/api/session/${token}`,title=document.querySelector('#title'),meta=document.querySelector('#meta'),controls=document.querySelector('#controls'),statusBox=document.querySelector('#status'),player=document.querySelector('#player'),actions=document.querySelector('#actions');
async function get(path=''){const r=await fetch(api+path,{cache:'no-store'});const j=await r.json();if(!r.ok)throw Error(j.error||'Request failed');return j}
function showReady(j){statusBox.textContent=`Ready · ${(j.size/1048576).toFixed(1)} MB`;controls.replaceChildren();player.replaceChildren();const ext=(j.filename||'').split('.').pop().toLowerCase();if(['mp4','webm','mov','m4v','mkv'].includes(ext)){const v=document.createElement('video');v.controls=true;v.playsInline=true;v.src=j.preview_url;player.append(v)}else if(['jpg','jpeg','png','webp','gif'].includes(ext)){const i=document.createElement('img');i.src=j.preview_url;i.alt=j.filename;player.append(i)}actions.replaceChildren();const d=document.createElement('a');d.className='action';d.href=j.download_url;d.textContent='⬇️ Download to this device';actions.append(d);const c=document.createElement('button');c.textContent='☁️ Save to my Telegram Cloud';c.onclick=saveCloud;actions.append(c)}
async function refresh(){try{const j=await get('/status');if(j.status==='ready'){showReady(j);return true}if(j.status==='error'){statusBox.textContent='Error: '+j.error;return true}if(j.status==='running')statusBox.textContent=j.message||'Preparing…'}catch(e){statusBox.textContent=e.message;return true}return false}
async function start(){const q=document.querySelector('#quality')?.value||'720';const b=document.querySelector('#prepare');if(b)b.disabled=true;statusBox.textContent='Downloading/preparing media… keep this page open.';try{await fetch(api+'/prepare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({quality:q})});const timer=setInterval(async()=>{if(await refresh())clearInterval(timer)},1800)}catch(e){statusBox.textContent=e.message;if(b)b.disabled=false}}
async function saveCloud(event){const button=event?.currentTarget;if(button)button.disabled=true;statusBox.textContent='Saving to your active Telegram cloud group…';try{const r=await fetch(api+'/save',{method:'POST'});const j=await r.json();if(!r.ok)throw Error(j.error||'Save failed');statusBox.textContent=`✅ Added to ${j.group_name||'your Telegram cloud group'}.`}catch(e){statusBox.textContent=e.message}finally{if(button)button.disabled=false}}
async function init(){try{const s=await get();title.textContent=s.title||'Media download';meta.textContent=[s.source,s.uploader,s.duration?`${Math.floor(s.duration/60)}:${String(s.duration%60).padStart(2,'0')}`:''].filter(Boolean).join(' · ');if(s.source==='file'){await refresh();return}const sel=document.createElement('select');sel.id='quality';for(const q of ['1080','720','480','360']){const o=document.createElement('option');o.value=q;o.textContent=q+'p MP4';sel.append(o)}controls.append(sel);const b=document.createElement('button');b.id='prepare';b.textContent='▶ Prepare preview & download';b.onclick=start;controls.append(b);statusBox.textContent='Choose quality and prepare. Long videos may take time; the file stays on the bot device until ready.';await refresh()}catch(e){statusBox.textContent=e.message}}
init();
</script></body></html>'''

_WEB_HOME = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>Telegram Media Hub</title><style>*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:20px;background:#10131c;color:#f3f5fa;font:16px system-ui,Arial,sans-serif}main{width:min(100%,620px);padding:26px;background:#1b2030;border:1px solid #343b50;border-radius:20px}h1{margin-top:0}li{margin:12px 0;color:#c7cde0}.tag{display:inline-block;background:#343b52;padding:7px 11px;border-radius:20px;margin:4px}</style></head><body><main><h1>🎬 Telegram Media Hub</h1><p>Open this page from the website button sent by your Telegram bot. Your source link is carried over automatically—no need to paste it here again.</p><h3>How to use</h3><ol><li>Send a supported link to your bot: <code>/yt</code>, <code>/insta</code>, <code>/pin</code>, <code>/github</code>, or <code>/gdrive</code>.</li><li>For long videos, tap <b>Play / Download on Website</b>, then choose quality.</li><li>Preview/play the prepared media, download it, or save it to your connected Telegram cloud group.</li></ol><div><span class="tag">YouTube</span><span class="tag">Instagram</span><span class="tag">Pinterest</span><span class="tag">GitHub</span><span class="tag">Google Drive</span></div></main></body></html>'''


class PublicDownloadService:
    def __init__(self):
        self._base_url = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
        self._port = int(os.getenv("PUBLIC_DOWNLOAD_PORT", "8765"))
        self._server = None
        self._tunnel = None
        self._lock = threading.Lock()
        self._downloads = {}
        self._web_sessions = {}
        self._universal_codes_loaded = False
        self._premium_attempts = {}
        self._download_dir = None
        self._ready_event = threading.Event()
        if self._base_url:
            self._ready_event.set()

    @property
    def ready(self):
        return bool(self._base_url)

    def start(self):
        """Start localhost HTTP and, when available, a temporary HTTPS tunnel."""
        if self._server:
            return self._base_url

        from config import DOWNLOAD_DIR
        self._download_dir = Path(DOWNLOAD_DIR).resolve()
        store_codes_path = Path(__file__).resolve().parent.parent / "universal_store_codes.txt"
        if not store_codes_path.is_file():
            print("⚠️ Universal Store code list missing: copy universal_store_codes.txt beside bot.py; app premium verification will fail until added.")

        service = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_args):
                pass

            def do_HEAD(self):
                if self.path.startswith(("/d/", "/p/")):
                    self._serve_file(send_body=False)
                else:
                    self.send_error(404)

            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                route = parsed.path.strip("/").split("/")
                if parsed.path == "/":
                    payload = _WEB_HOME.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(payload)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(payload)
                elif len(route) == 2 and route[0] == "w":
                    self._serve_web_page(route[1])
                elif len(route) == 3 and route[0] == "api" and route[1] == "session":
                    self._serve_session_api(route[2], include_status=False)
                elif len(route) == 4 and route[:2] == ["api", "session"] and route[3] == "status":
                    self._serve_session_api(route[2], include_status=True)
                elif route and route[0] in ("d", "p"):
                    self._serve_file(send_body=True)
                else:
                    self.send_error(404)

            def do_POST(self):
                route = urllib.parse.urlparse(self.path).path.strip("/").split("/")
                if route == ["api", "premium", "redeem"]:
                    self._redeem_premium_code()
                    return
                if len(route) != 4 or route[0] != "api" or route[1] != "session":
                    self.send_error(404)
                    return
                session = service._get_web_session(route[2])
                if not session:
                    self._send_json({"error": "This website session expired. Send the Telegram link again."}, 404)
                    return
                if route[3] == "prepare":
                    self._prepare_web_session(route[2], session)
                elif route[3] == "save":
                    self._save_to_cloud(route[2], session)
                else:
                    self.send_error(404)

            def _redeem_premium_code(self):
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length < 1 or length > 1024:
                        self._send_json({"status": "invalid_request"}, 400)
                        return
                    payload = json.loads(self.rfile.read(length))
                    code = str(payload.get("code", "")).strip().upper()
                    install_id = str(payload.get("install_id", "")).strip()
                    if not re.fullmatch(r"[A-Z0-9]{6}", code) or not re.fullmatch(r"[A-Fa-f0-9-]{32,36}", install_id):
                        self._send_json({"status": "invalid_request"}, 400)
                        return
                    remote = self.headers.get("CF-Connecting-IP", "").strip() or self.client_address[0]
                    if not service._allow_premium_attempt(remote):
                        self._send_json({"status": "rate_limited"}, 429)
                        return
                    status = service._redeem_universal_store_code(code, install_id)
                    self._send_json({"status": status}, 200 if status == "success" else 409)
                except (ValueError, TypeError, json.JSONDecodeError):
                    self._send_json({"status": "invalid_request"}, 400)
                except Exception:
                    logger.exception("Universal Store premium verification failed")
                    self._send_json({"status": "server_error"}, 500)

            def _send_json(self, data, status=200):
                payload = json.dumps(data).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(payload)

            def _serve_web_page(self, token):
                if not service._get_web_session(token):
                    self.send_error(404, "Website session expired")
                    return
                payload = _WEB_PAGE.replace("__SESSION__", json.dumps(token)).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(payload)

            def _serve_session_api(self, token, include_status=False):
                session = service._get_web_session(token)
                if not session:
                    self._send_json({"error": "Website session expired"}, 404)
                    return
                if include_status:
                    job = dict(session.get("job") or {"status": "idle"})
                    job.pop("filepath", None)
                    self._send_json(job)
                else:
                    self._send_json({
                        "source": session["source"],
                        "title": session.get("title") or "Your download",
                        "uploader": session.get("uploader") or "",
                        "duration": session.get("duration") or 0,
                    })

            def _prepare_web_session(self, token, session):
                if session.get("source") == "file":
                    job = dict(session.get("job") or {"status": "error", "error": "File is unavailable"})
                    job.pop("filepath", None)
                    self._send_json(job)
                    return
                try:
                    length = min(int(self.headers.get("Content-Length", "0")), 2048)
                    body = json.loads(self.rfile.read(length) or b"{}")
                    quality = str(body.get("quality") or "720")
                except Exception:
                    quality = "720"
                if quality not in {"1080", "720", "480", "360"}:
                    quality = "720"
                with service._lock:
                    job = session.get("job") or {"status": "idle"}
                    if job.get("status") in {"running", "ready"}:
                        response = dict(job)
                        response.pop("filepath", None)
                        self._send_json(response)
                        return
                    session["job"] = {"status": "running", "message": "Preparing your media…"}
                threading.Thread(
                    target=service._prepare_web_session,
                    args=(token, quality),
                    name="web-media-download",
                    daemon=True,
                ).start()
                self._send_json(session["job"], 202)

            def _save_to_cloud(self, token, session):
                job = session.get("job") or {}
                filepath = job.get("filepath")
                user_id = session.get("user_id")
                if not filepath or not Path(filepath).is_file() or not user_id:
                    self._send_json({"error": "Prepare the download first."}, 400)
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length > 2048:
                        self._send_json({"error": "Invalid request"}, 400)
                        return
                    if length:
                        self.rfile.read(length)
                    result = service._save_file_to_telegram_cloud(int(user_id), filepath, session.get("title", "Media"))
                    self._send_json(result, 200 if result.get("success") else 400)
                except Exception as exc:
                    self._send_json({"error": str(exc)}, 500)

            def _serve_file(self, send_body):
                route = urllib.parse.urlparse(self.path).path.strip("/").split("/")
                route_type = route[0] if route else ""
                token = route[1] if len(route) >= 2 and route_type in ("d", "p") else ""
                with service._lock:
                    item = service._downloads.get(token)
                    if item and item["expires"] <= time.time():
                        service._downloads.pop(token, None)
                        item = None
                if not item:
                    self.send_error(404, "Download link expired or invalid")
                    return

                path = item["path"]
                try:
                    size = path.stat().st_size
                    start, end, status = 0, size - 1, 200
                    range_header = self.headers.get("Range", "")
                    match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
                    if match:
                        if not match.group(1):
                            length = int(match.group(2) or 0)
                            start = max(0, size - length)
                        else:
                            start = int(match.group(1))
                        if match and match.group(2) and match.group(1):
                            end = min(size - 1, int(match.group(2)))
                        if start >= size or start > end:
                            self.send_response(416)
                            self.send_header("Content-Range", f"bytes */{size}")
                            self.send_header("Content-Length", "0")
                            self.end_headers()
                            return
                        status = 206

                    length = max(0, end - start + 1)
                    filename = item["name"]
                    quoted = urllib.parse.quote(filename)
                    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename) or "download"
                    self.send_response(status)
                    self.send_header("Content-Type", mimetypes.guess_type(filename)[0] or "application/octet-stream")
                    disposition = "inline" if route_type == "p" else "attachment"
                    self.send_header("Content-Disposition", f"{disposition}; filename=\"{safe_name}\"; filename*=UTF-8''{quoted}")
                    self.send_header("Content-Length", str(length))
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Cache-Control", "private, no-store")
                    if status == 206:
                        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                    self.end_headers()
                    if send_body:
                        with path.open("rb") as file_obj:
                            file_obj.seek(start)
                            remaining = length
                            while remaining:
                                block = file_obj.read(min(1024 * 1024, remaining))
                                if not block:
                                    break
                                self.wfile.write(block)
                                remaining -= len(block)
                except (OSError, BrokenPipeError, ConnectionResetError):
                    return

        self._server = ThreadingHTTPServer(("127.0.0.1", self._port), Handler)
        self._server.daemon_threads = True
        self._port = self._server.server_address[1]
        threading.Thread(target=self._server.serve_forever, name="public-download-http", daemon=True).start()
        threading.Thread(target=self._cleanup_expired, name="public-download-cleanup", daemon=True).start()

        if self._base_url:
            print(f"🔗 Public download server uses configured URL: {self._base_url}")
            print(f"💎 Universal Store verification API: {self._base_url}/api/premium/redeem")
            return self._base_url
        cloudflared = self._find_cloudflared()
        if not cloudflared:
            print("📦 cloudflared not found; trying platform installer in the background. Bot startup will not wait.")
            threading.Thread(target=self._install_and_launch_tunnel, name="cloudflared-setup", daemon=True).start()
            return ""

        self._launch_tunnel(cloudflared)
        return ""

    def _install_and_launch_tunnel(self):
        try:
            if os.path.isdir("/data/data/com.termux"):
                pkg = shutil.which("pkg")
                if not pkg:
                    raise RuntimeError("Termux pkg command not found; run `pkg install cloudflared`.")
                subprocess.run([pkg, "install", "-y", "cloudflared"], check=True, timeout=300)
            elif os.name == "nt":
                winget = shutil.which("winget")
                if not winget:
                    raise RuntimeError("winget not found; run `winget install --id Cloudflare.cloudflared`.")
                subprocess.run(
                    [winget, "install", "--id", "Cloudflare.cloudflared", "-e", "--silent",
                     "--accept-package-agreements", "--accept-source-agreements"],
                    check=True,
                    timeout=300,
                    capture_output=True,
                    text=True,
                )
            cloudflared = self._find_cloudflared()
            if not cloudflared:
                raise RuntimeError("cloudflared installation finished but the executable was not found.")
            self._launch_tunnel(cloudflared)
        except Exception as exc:
            print(f"⚠️ Direct HTTPS setup failed: {exc}")
            if os.name == "nt":
                print("Install manually with: winget install --id Cloudflare.cloudflared")
            elif os.path.isdir("/data/data/com.termux"):
                print("Install manually with: pkg install cloudflared")

    @staticmethod
    def _find_cloudflared():
        cloudflared = shutil.which("cloudflared")
        if cloudflared or os.name != "nt":
            return cloudflared
        program_files = os.getenv("ProgramFiles(x86)") or os.getenv("ProgramFiles") or "C:\\Program Files"
        candidate = Path(program_files) / "cloudflared" / "cloudflared.exe"
        return str(candidate) if candidate.is_file() else None

    def _launch_tunnel(self, cloudflared):
        command = [cloudflared, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{self._port}"]
        popen_options = {"stdout": subprocess.PIPE, "stderr": subprocess.STDOUT, "text": True, "bufsize": 1}
        if os.name == "nt":
            popen_options["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self._tunnel = subprocess.Popen(command, **popen_options)

        def read_tunnel_output():
            if not self._tunnel or not self._tunnel.stdout:
                return
            for line in self._tunnel.stdout:
                match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if match:
                    self._base_url = match.group(0)
                    self._ready_event.set()
                    print(f"🌐 Temporary HTTPS download URL ready: {self._base_url}")
                    print(f"💎 Universal Store verification API: {self._base_url}/api/premium/redeem")
                elif "ERR" in line or "error" in line.lower():
                    print(f"Cloudflare Tunnel: {line.strip()}")

        threading.Thread(target=read_tunnel_output, name="cloudflared-output", daemon=True).start()
        print("⏳ Cloudflare Quick Tunnel is connecting in the background; the bot will continue starting.")

    def _allow_premium_attempt(self, remote):
        """Limit code guesses per client IP to slow brute-force attempts."""
        now = time.time()
        with self._lock:
            attempts = [timestamp for timestamp in self._premium_attempts.get(remote, []) if now - timestamp < 3600]
            if len(attempts) >= 12:
                self._premium_attempts[remote] = attempts
                return False
            attempts.append(now)
            self._premium_attempts[remote] = attempts
            return True

    def _redeem_universal_store_code(self, code, install_id):
        from database import db

        with self._lock:
            if not self._universal_codes_loaded:
                codes_path = Path(__file__).resolve().parent.parent / "universal_store_codes.txt"
                if not codes_path.is_file():
                    raise FileNotFoundError("Universal Store code registry is missing")
                codes = codes_path.read_text(encoding="utf-8").splitlines()
                db.import_universal_store_codes(codes)
                self._universal_codes_loaded = True
        return db.redeem_universal_store_code(code, install_id)

    async def wait_until_ready(self, timeout=45):
        if self.ready:
            return True
        try:
            return await asyncio.to_thread(self._ready_event.wait, timeout)
        except Exception:
            return False

    def create_web_session(self, source, url, user_id, title="", uploader="", duration=0, filepath=None):
        if not self.ready or not self._server:
            return None
        allowed_sources = {"youtube", "instagram", "pinterest", "github", "drive", "file"}
        if source not in allowed_sources or (source != "file" and not str(url or "").startswith(("https://", "http://"))):
            return None
        token = uuid.uuid4().hex + uuid.uuid4().hex
        session = {
            "source": source,
            "url": url,
            "user_id": int(user_id) if user_id else None,
            "title": str(title or "Your download")[:300],
            "uploader": str(uploader or "")[:200],
            "duration": int(duration or 0),
            "expires": time.time() + 2 * 60 * 60,
            "job": {"status": "idle"},
        }
        with self._lock:
            self._web_sessions[token] = session
        if filepath:
            self._complete_web_session(token, filepath)
        return f"{self._base_url}/w/{token}"

    def _get_web_session(self, token):
        with self._lock:
            session = self._web_sessions.get(token)
            if session and session["expires"] <= time.time():
                self._web_sessions.pop(token, None)
                return None
            return session

    def _prepare_web_session(self, token, quality):
        session = self._get_web_session(token)
        if not session:
            return
        try:
            from services.downloader_service import downloader_service
            source, url = session["source"], session["url"]
            if source == "youtube":
                result = downloader_service._download_youtube_sync(url, quality)
            elif source == "instagram":
                result = downloader_service._download_instagram_sync(url)
                result = result[0] if result else None
            elif source == "pinterest":
                result = downloader_service._download_pinterest_sync(url, "video")
            elif source == "github":
                result = downloader_service._download_github_repo_sync(url)
            elif source == "drive":
                result = downloader_service._download_gdrive_sync(url)
            else:
                result = None
            if isinstance(result, list):
                result = result[0] if result else None
            if not result or not result.get("filepath"):
                raise RuntimeError("The source could not provide a downloadable file.")
            session["title"] = result.get("title") or result.get("filename") or session.get("title")
            self._complete_web_session(token, result["filepath"], result.get("filename"))
        except Exception as exc:
            with self._lock:
                if token in self._web_sessions:
                    self._web_sessions[token]["job"] = {"status": "error", "error": str(exc)[:400]}

    def _complete_web_session(self, token, filepath, filename=None):
        path = Path(filepath).resolve()
        if not path.is_file():
            raise FileNotFoundError("Prepared media file was not found.")
        file_url = self.create_link(path, filename=filename or path.name)
        if not file_url:
            raise RuntimeError("The public download tunnel is not ready.")
        file_token = urllib.parse.urlparse(file_url).path.strip("/").split("/")[1]
        session = self._get_web_session(token)
        if not session:
            return
        session["job"] = {
            "status": "ready",
            "filename": filename or path.name,
            "size": path.stat().st_size,
            "filepath": str(path),
            "download_url": file_url,
            "preview_url": f"{self._base_url}/p/{file_token}/{urllib.parse.quote(filename or path.name)}",
        }

    def _save_file_to_telegram_cloud(self, user_id, filepath, title):
        async def save():
            from database import db
            from services.telegram_storage_service import storage_service
            group = db.get_user_active_cloud_group(user_id)
            if not group:
                return {"success": False, "error": "No active Telegram cloud group. Connect /storage first."}
            client = await storage_service.get_authorized_client(user_id)
            if not client:
                return {
                    "success": False,
                    "error": "Telegram session authorization failed. In the bot, send /storage → Disconnect Account → Yes, Disconnect, then send /storage and connect again. Stop any other PC/Termux copy of this bot first, so only one instance uses the session.",
                }
            try:
                # Keep Telethon's marked -100... channel ID. Stripping the
                # prefix turns it into an unmarked positive ID, which can be
                # interpreted as a user ID instead of the cloud supergroup.
                entity = await client.get_entity(int(group["telegram_chat_id"]))
                await client.send_file(entity, filepath, caption=str(title or "Media")[:900])
                return {"success": True, "group_name": group.get("group_name", "your cloud group")}
            except Exception as exc:
                logger.exception("Website cloud save failed for user %s", user_id)
                return {"success": False, "error": f"Could not add the file to '{group.get('group_name', 'your cloud group')}': {exc}"}
            finally:
                await client.disconnect()

        return asyncio.run(save())

    def create_link(self, filepath, filename=None, ttl_seconds=2 * 60 * 60):
        if not self.ready or not self._download_dir:
            return None
        path = Path(filepath).resolve()
        if not path.is_file() or path.parent != self._download_dir:
            return None
        token = uuid.uuid4().hex + uuid.uuid4().hex
        safe_filename = Path(filename or path.name).name
        with self._lock:
            self._downloads[token] = {"path": path, "name": safe_filename, "expires": time.time() + ttl_seconds}
        return f"{self._base_url}/d/{token}/{urllib.parse.quote(safe_filename)}"

    def _cleanup_expired(self):
        while self._server:
            time.sleep(60)
            now = time.time()
            with self._lock:
                expired = [item for item in self._downloads.values() if item["expires"] <= now]
                self._downloads = {key: item for key, item in self._downloads.items() if item["expires"] > now}
                live_paths = {item["path"] for item in self._downloads.values()}
            for item in expired:
                path = item["path"]
                if path not in live_paths and self._download_dir and path.parent == self._download_dir:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._tunnel and self._tunnel.poll() is None:
            self._tunnel.terminate()
            try:
                self._tunnel.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._tunnel.kill()
            self._tunnel = None


public_download_service = PublicDownloadService()
