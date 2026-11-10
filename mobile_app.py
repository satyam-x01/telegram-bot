#!/usr/bin/env python3
"""
Telegram Bot 24/7 Mobile Host & Controller App
===============================================
Made by Satyam

Provides a modern mobile-optimized Web App dashboard to run, monitor,
and control the Telegram Bot 24/7 with zero command-line interaction.
"""

import os
import sys
import json
import time
import signal
import subprocess
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

BASE_DIR = Path(__file__).parent.resolve()
CRED_FILE = BASE_DIR / ".bot_credentials.json"
BOT_SCRIPT = BASE_DIR / "bot.py"

# Process state
bot_process = None
log_history = []
MAX_LOGS = 150


def append_log(line: str):
    clean = line.strip()
    if clean:
        timestamp = time.strftime("[%H:%M:%S] ")
        log_history.append(timestamp + clean)
        if len(log_history) > MAX_LOGS:
            log_history.pop(0)


def load_credentials():
    if CRED_FILE.exists():
        try:
            with open(CRED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", "")
    }


def save_credentials(bot_token: str, gemini_api_key: str):
    data = {
        "bot_token": bot_token.strip(),
        "gemini_api_key": gemini_api_key.strip()
    }
    with open(CRED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


def log_reader_thread(proc):
    try:
        for line in iter(proc.stdout.readline, ''):
            if not line:
                break
            append_log(line)
    except Exception:
        pass


def start_bot_process():
    global bot_process
    if bot_process and bot_process.poll() is None:
        return False, "Bot is already running!"

    creds = load_credentials()
    if not creds.get("bot_token"):
        return False, "Please enter your Telegram Bot Token first!"

    env = os.environ.copy()
    env["TELEGRAM_BOT_TOKEN"] = creds["bot_token"]
    if creds.get("gemini_api_key"):
        env["GEMINI_API_KEY"] = creds["gemini_api_key"]
    env["PYTHONUNBUFFERED"] = "1"

    append_log("🚀 Starting 24/7 Telegram Bot process...")

    cmd = [sys.executable, str(BOT_SCRIPT)]
    bot_process = subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    t = threading.Thread(target=log_reader_thread, args=(bot_process,), daemon=True)
    t.start()
    return True, "Bot started successfully!"


def stop_bot_process():
    global bot_process
    if not bot_process or bot_process.poll() is not None:
        bot_process = None
        return False, "Bot is not running."

    append_log("⏹ Stopping Telegram Bot process...")
    try:
        bot_process.terminate()
        bot_process.wait(timeout=5)
    except Exception:
        try:
            bot_process.kill()
        except Exception:
            pass
    bot_process = None
    append_log("🔴 Bot process stopped.")
    return True, "Bot stopped."


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Telegram Bot 24/7 Host</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: rgba(20, 26, 43, 0.85);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --green: #22c55e;
      --red: #ef4444;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 16px;
      background-image: radial-gradient(circle at 50% 0%, rgba(56, 189, 248, 0.15), transparent 45%);
    }
    .app-container {
      width: 100%;
      max-width: 480px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .header-card {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 20px;
      text-align: center;
      position: relative;
    }
    .logo-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 56px;
      height: 56px;
      border-radius: 16px;
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      font-size: 28px;
      margin-bottom: 12px;
      box-shadow: 0 8px 24px rgba(56, 189, 248, 0.35);
    }
    h1 { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
    .subtitle { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-top: 14px;
      padding: 6px 16px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .status-running {
      background: rgba(34, 197, 94, 0.15);
      color: var(--green);
      border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .status-stopped {
      background: rgba(239, 68, 68, 0.15);
      color: var(--red);
      border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
    }
    .status-running .dot {
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
    }
    .card {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 18px;
    }
    .section-title {
      font-size: 14px;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .form-group {
      margin-bottom: 14px;
    }
    label {
      display: block;
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 6px;
    }
    input[type="text"], input[type="password"] {
      width: 100%;
      background: rgba(11, 15, 25, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 12px;
      padding: 12px 14px;
      color: var(--text);
      font-size: 13px;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s;
    }
    input:focus {
      border-color: var(--primary);
    }
    .btn {
      width: 100%;
      border: none;
      border-radius: 14px;
      padding: 14px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: transform 0.1s, opacity 0.2s;
    }
    .btn:active { transform: scale(0.98); }
    .btn-primary {
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      color: #fff;
      box-shadow: 0 4px 20px rgba(56, 189, 248, 0.3);
    }
    .btn-danger {
      background: linear-gradient(135deg, #dc2626, #ef4444);
      color: #fff;
      box-shadow: 0 4px 20px rgba(239, 68, 68, 0.3);
    }
    .btn-secondary {
      background: rgba(255, 255, 255, 0.08);
      color: var(--text);
      margin-top: 8px;
    }
    .log-box {
      background: #060911;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 12px;
      height: 180px;
      overflow-y: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: #38bdf8;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-all;
    }
    .tips-list {
      list-style: none;
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.6;
    }
    .tips-list li {
      margin-bottom: 6px;
      display: flex;
      align-items: flex-start;
      gap: 8px;
    }
    .satyam-footer {
      margin-top: 18px;
      text-align: center;
      padding: 14px;
      background: linear-gradient(90deg, rgba(56, 189, 248, 0.05), rgba(168, 85, 247, 0.05));
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 16px;
      font-size: 13px;
      color: var(--text);
      letter-spacing: 0.3px;
    }
    .satyam-footer strong {
      background: linear-gradient(135deg, #38bdf8, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      font-weight: 800;
    }
  </style>
</head>
<body>
  <div class="app-container">
    <div class="header-card">
      <div class="logo-badge">🤖</div>
      <h1>Telegram Bot 24/7</h1>
      <p class="subtitle">Protected Academic & Space AI System</p>
      <div id="statusPill" class="status-pill status-stopped">
        <span class="dot"></span>
        <span id="statusText">🔴 Bot Stopped</span>
      </div>
    </div>

    <div class="card">
      <div class="section-title">🔑 Bot Credentials</div>
      <div class="form-group">
        <label>Telegram Bot Token</label>
        <input type="password" id="botToken" placeholder="Paste bot token from @BotFather">
      </div>
      <div class="form-group">
        <label>Gemini AI API Key</label>
        <input type="password" id="geminiKey" placeholder="Paste Gemini API Key">
      </div>
      <button class="btn btn-secondary" onclick="saveCreds()">💾 Save Credentials</button>
    </div>

    <div class="card">
      <div class="section-title">⚡ Controls</div>
      <button id="toggleBtn" class="btn btn-primary" onclick="toggleBot()">
        🚀 START BOT (24/7)
      </button>
    </div>

    <div class="card">
      <div class="section-title">📋 Live Console Logs</div>
      <div id="logBox" class="log-box">Waiting for bot to start...</div>
    </div>

    <div class="card">
      <div class="section-title">🔋 24/7 Android Background Setup</div>
      <ul class="tips-list">
        <li>🔔 <strong>Notification:</strong> Keep Termux / host notification enabled in status bar.</li>
        <li>⚡ <strong>Battery Optimization:</strong> Set App Battery usage to <em>"Unrestricted / No Restrictions"</em>.</li>
        <li>📶 <strong>Data Usage:</strong> Enable <em>"Unrestricted Data / Background Data"</em>.</li>
      </ul>
    </div>

    <div class="satyam-footer">
      Made with ❤️ by <strong>Satyam</strong>
    </div>
  </div>

  <script>
    let isRunning = false;

    async function fetchStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        isRunning = data.running;
        
        const pill = document.getElementById('statusPill');
        const txt = document.getElementById('statusText');
        const btn = document.getElementById('toggleBtn');
        const logBox = document.getElementById('logBox');

        if (isRunning) {
          pill.className = 'status-pill status-running';
          txt.textContent = '🟢 Online 24/7';
          btn.className = 'btn btn-danger';
          btn.textContent = '⏹ STOP BOT';
        } else {
          pill.className = 'status-pill status-stopped';
          txt.textContent = '🔴 Bot Stopped';
          btn.className = 'btn btn-primary';
          btn.textContent = '🚀 START BOT (24/7)';
        }

        if (data.logs && data.logs.length > 0) {
          logBox.textContent = data.logs.join('\\n');
          logBox.scrollTop = logBox.scrollHeight;
        }

        if (data.token && !document.getElementById('botToken').value) {
          document.getElementById('botToken').value = data.token;
        }
        if (data.gemini && !document.getElementById('geminiKey').value) {
          document.getElementById('geminiKey').value = data.gemini;
        }
      } catch (err) {
        console.error('Fetch status error:', err);
      }
    }

    async function saveCreds() {
      const token = document.getElementById('botToken').value;
      const gemini = document.getElementById('geminiKey').value;
      const res = await fetch('/api/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ bot_token: token, gemini_api_key: gemini })
      });
      const data = await res.json();
      alert(data.message || 'Credentials Saved!');
    }

    async function toggleBot() {
      if (isRunning) {
        await fetch('/api/stop', { method: 'POST' });
      } else {
        const token = document.getElementById('botToken').value;
        const gemini = document.getElementById('geminiKey').value;
        await fetch('/api/save', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ bot_token: token, gemini_api_key: gemini })
        });
        const res = await fetch('/api/start', { method: 'POST' });
        const data = await res.json();
        if (!data.success) {
          alert(data.message);
        }
      }
      fetchStatus();
    }

    fetchStatus();
    setInterval(fetchStatus, 2000);
  </script>
</body>
</html>
"""


class BotRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy HTTP request console logging
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            creds = load_credentials()
            running = bot_process is not None and bot_process.poll() is None
            resp = {
                "running": running,
                "logs": log_history,
                "token": creds.get("bot_token", ""),
                "gemini": creds.get("gemini_api_key", "")
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        parsed = urllib.parse.urlparse(self.path)

        data = {}
        if body:
            try:
                data = json.loads(body)
            except Exception:
                pass

        if parsed.path == "/api/save":
            saved = save_credentials(data.get("bot_token", ""), data.get("gemini_api_key", ""))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "Credentials saved successfully!"}).encode("utf-8"))

        elif parsed.path == "/api/start":
            success, msg = start_bot_process()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "message": msg}).encode("utf-8"))

        elif parsed.path == "/api/stop":
            success, msg = stop_bot_process()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "message": msg}).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()


def run_server(port=8080):
    server_address = ("", port)
    try:
        httpd = HTTPServer(server_address, BotRequestHandler)
    except OSError:
        port = 8081
        server_address = ("", port)
        httpd = HTTPServer(server_address, BotRequestHandler)

    print(f"\n" + "=" * 55)
    print(f"🤖 Telegram Bot 24/7 Mobile Controller is Active!")
    print(f"📱 Open on your mobile phone or browser:")
    print(f"   👉 http://localhost:{port}")
    print(f"✨ Made with ❤️ by Satyam")
    print("=" * 55 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        stop_bot_process()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
