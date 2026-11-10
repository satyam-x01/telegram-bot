#!/data/data/com.termux/files/usr/bin/bash
# Animated, restart-safe Termux bot runner.

set -u
PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$PROJECT_DIR" || exit 1

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; PURPLE='\033[0;35m'; NC='\033[0m'

cleanup() {
  printf "\n${YELLOW}Stopping bot safely…${NC}\n"
  [ -n "${BOT_PID:-}" ] && kill "$BOT_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

loading() {
  clear
  printf "${CYAN}\n╔══════════════════════════════════════════════╗\n"
  printf "║         SHIBH TELEGRAM BOT • 24/7            ║\n"
  printf "╚══════════════════════════════════════════════╝${NC}\n\n"
  for frame in '◜' '◠' '◝' '◞' '◡' '◟'; do
    printf "\r${PURPLE}%s${NC} Loading secure bot services…" "$frame"
    sleep 0.12
  done
  printf "\r${GREEN}✓${NC} Loading secure bot services… ready!        \n"
}

if [ ! -f "bot.py" ]; then
  printf "${RED}✗ bot.py is missing. Run this from the project folder.${NC}\n"
  exit 1
fi

if ! python -c "import telegram, yt_dlp, telethon" >/dev/null 2>&1; then
  printf "${RED}✗ Dependencies are missing. Run: bash start.sh${NC}\n"
  exit 1
fi

if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock
fi

session=0
while true; do
  session=$((session + 1))
  loading
  printf "${CYAN}Session #${session}${NC}  ${GREEN}Starting bot…${NC}\n"
  printf "${YELLOW}Press Ctrl+C once to stop.${NC}\n\n"

  python -u bot.py &
  BOT_PID=$!
  wait "$BOT_PID"
  exit_code=$?
  BOT_PID=""

  if [ "$exit_code" -eq 0 ]; then
    printf "${YELLOW}\nBot stopped normally. Restarting in 5 seconds…${NC}\n"
  else
    printf "${RED}\nBot exited (code ${exit_code}). Restarting in 8 seconds…${NC}\n"
  fi
  sleep 8
done
