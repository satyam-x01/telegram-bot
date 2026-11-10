#!/data/data/com.termux/files/usr/bin/bash
# One-time Termux setup, followed by the animated bot runner.

set -u
PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$PROJECT_DIR" || exit 1

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

banner() {
  clear
  printf "${CYAN}\n"
  printf "╔══════════════════════════════════════════════╗\n"
  printf "║       SHIBH TELEGRAM BOT • TERMUX SETUP      ║\n"
  printf "╚══════════════════════════════════════════════╝\n${NC}\n"
}

step() { printf "${CYAN}➜${NC} %s\n" "$1"; }
ok() { printf "${GREEN}✓${NC} %s\n" "$1"; }
warn() { printf "${YELLOW}!${NC} %s\n" "$1"; }
fail() { printf "${RED}✗${NC} %s\n" "$1"; }

banner

if ! command -v pkg >/dev/null 2>&1; then
  fail "Run this script inside the Termux app."
  exit 1
fi

step "Updating Termux packages…"
pkg update -y || warn "Package update skipped; continuing with installed packages."

step "Installing Python, FFmpeg and build libraries…"
if ! pkg install -y python ffmpeg git openssl libffi; then
  fail "System package installation failed. Run: termux-change-repo, then try again."
  exit 1
fi
ok "System packages are ready"

step "Updating Python installer…"
python -m pip install --upgrade pip setuptools wheel || {
  fail "pip update failed. Check your internet connection and retry."
  exit 1
}

# Install Android/Termux-compatible runtime dependencies. Gemini uses the REST
# API through requests, avoiding unsupported Rust-native SDK build dependencies.
# Termux supplies the native ffmpeg binary through pkg.
step "Installing Python libraries (first run may take a few minutes)…"
if ! python -m pip install \
  "python-telegram-bot[job-queue]>=20.8" \
  "yt-dlp>=2024.12.13" \
  "python-dotenv>=1.0.1" \
  "aiofiles>=23.2.1" \
  "requests>=2.31.0" \
  "gdown>=6.4.0" \
  "telethon>=1.36.0"; then
  fail "Python dependency installation failed. Run the script again after checking internet/storage."
  exit 1
fi
ok "All bot dependencies are installed"
ok "Gemini AI uses the built-in REST client — no Rust build required"

if [ ! -f "bot.py" ]; then
  fail "bot.py was not found in: $PROJECT_DIR"
  exit 1
fi

step "Running full compatibility check…"
if ! command -v ffmpeg >/dev/null 2>&1; then
  fail "FFmpeg is missing. Run start.sh again so Termux can install it."
  exit 1
fi

if ! python -c "import telegram, yt_dlp, dotenv, aiofiles, requests, gdown, telethon; print('Python modules OK')"; then
  fail "A required Python module is unavailable. Run start.sh again."
  exit 1
fi

if ! python -m py_compile bot.py database.py services/ai_service.py handlers/*.py; then
  fail "Bot source validation failed. Copy the complete updated project and run start.sh again."
  exit 1
fi
ok "FFmpeg, Python modules and all bot files validated"

chmod +x bot.sh
ok "Setup complete"
printf "${GREEN}\nLaunching the animated 24/7 bot runner…${NC}\n"
sleep 1
exec ./bot.sh
