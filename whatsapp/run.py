import sys
import os
import webbrowser
from pathlib import Path

# Force UTF-8 encoding on Windows to ensure emojis and banners display reliably
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure root directory is in sys.path and bin is on PATH
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
bin_dir = str(root_dir / "bin")
if os.path.isdir(bin_dir) and bin_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")

from modules.config import config_manager, logger
from app import app, start_bot_client

import threading
from modules.tunnel import tunnel_manager

def main():
    port = config_manager.get("port", 5000)
    
    # Start Cloudflare Quick Tunnel in background thread so users outside local WiFi can access videos
    def start_tunnel_worker():
        try:
            cf_url = tunnel_manager.start_tunnel(port=port, wait_seconds=15)
            if cf_url:
                print(f"\n🚀 [Cloudflare Tunnel Online] Public Video Portal URL: {cf_url}", flush=True)
                print(f"👉 Watch Page: {cf_url}/watch\n", flush=True)
            else:
                print("\n[!] Cloudflare Tunnel not available; falling back to LAN IP.", flush=True)
        except Exception as e:
            logger.warning(f"Cloudflare tunnel init error: {e}")

    threading.Thread(target=start_tunnel_worker, daemon=True).start()

    banner = f"""
========================================================================
🤖  SATYAM WHATSAPP AUTOMATION BOT & DISCOVERY FEED 24/7
========================================================================
🌐  Local Dashboard:         http://localhost:{port}
☁️  Cloudflare Tunnel:       Auto-starting (Public HTTPS for outside WiFi)
📱  WhatsApp QR Code:         Open dashboard to scan QR code
🔒  Master Password:          {config_manager.get('bot_password', 'satyam08052010')}
⏱️   Default Interval:         {config_manager.get('interval_minutes', 5)} minute(s)
🎥  Media Downloader:         YouTube & Instagram (Web Player + Multi-Quality)
🧠  AI Engine:                Google Gemini (Search & Chat & Vision)
========================================================================
[1] Starting WhatsApp socket client...
[2] Starting Cloudflare tunnel & Web Dashboard at http://localhost:{port}...
========================================================================
"""
    print(banner, flush=True)

    # Start WhatsApp client in background daemon thread
    start_bot_client()

    # Launch Flask Web Dashboard
    try:
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n[!] Shutting down WhatsApp Bot gracefully. Bye!")
        tunnel_manager.stop_tunnel()

if __name__ == "__main__":
    main()
