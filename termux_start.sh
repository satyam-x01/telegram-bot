#!/bin/bash
# Use the maintained Termux installer. The legacy launcher below is retained
# only for reference and is never reached.
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec "$SCRIPT_DIR/start.sh"

# Termux 24/7 Telegram Music Bot Auto-Launcher

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BRIGHT_BLACK='\033[90m'
NC='\033[0m' # No Color

# Clear screen
clear

# Loading screen with animation
loading_screen() {
    echo -e "${CYAN}"
    sleep 0.3
    echo -e "${BRIGHT_BLACK}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${NC}"
    sleep 0.1
    echo -e "${BRIGHT_BLACK}┃${NC}                                                            ${BRIGHT_BLACK}┃${NC}"
    sleep 0.1
    echo -e "${BRIGHT_BLACK}┃${PURPLE}         🎵  TELEGRAM MUSIC BOT - LOADING...  🎵           ${BRIGHT_BLACK}┃${NC}"
    sleep 0.1
    echo -e "${BRIGHT_BLACK}┃${NC}                                                            ${BRIGHT_BLACK}┃${NC}"
    sleep 0.1
    echo -e "${BRIGHT_BLACK}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${NC}"
    sleep 0.3
    
    echo ""
    
    # Animated loading bar with dots
    echo -e "${CYAN}Loading Beast Mode${NC}"
    for i in {1..5}; do
        echo -ne "\r${PURPLE}●${NC}$(printf '○%.0s' $(seq 1 $((5-i)))) "
        sleep 0.3
    done
    sleep 0.2
    echo ""
    
    # Loading bar with percentage
    local width=50
    for ((i=0; i<=width; i++)); do
        percent=$((i * 100 / width))
        bar=$(printf '█%.0s' $(seq 1 $i))
        empty=$(printf '░%.0s' $(seq 1 $((width - i))))
        echo -ne "\r${CYAN}[${bar}${empty}]${NC} ${YELLOW}${percent}%${NC} "
        sleep 0.05
    done
    echo ""
    sleep 0.2
    
    # Initializing text animation
    echo -e "${GREEN}Initializing Systems...${NC}"
    for i in {1..3}; do
        echo -ne "\r${CYAN}Initializing${NC}"
        for j in {1..3}; do
            echo -ne "."
            sleep 0.2
        done
        echo -ne "\r${CYAN}                   ${NC}\r"
    done
    echo -ne "\r${GREEN}✓ Systems Ready!${NC}\n"
    sleep 0.3
    
    # Pulsing effect
    echo ""
    echo -e "${BRIGHT_BLACK}┌─────────────────────────────────────────────────────────┐${NC}"
    sleep 0.1
    for i in {1..2}; do
        echo -ne "\r${BRIGHT_BLACK}│${NC}${GREEN}  ◆ Loading Core Modules ◆  ${NC}${BRIGHT_BLACK}│${NC}"
        sleep 0.2
        echo -ne "\r${BRIGHT_BLACK}│${NC}${YELLOW}  ◇ Loading Core Modules ◇  ${NC}${BRIGHT_BLACK}│${NC}"
        sleep 0.2
    done
    echo -ne "\r${BRIGHT_BLACK}│${NC}${GREEN}  ✓ Core Modules Loaded  ✓  ${NC}${BRIGHT_BLACK}│${NC}\n"
    sleep 0.1
    echo -e "${BRIGHT_BLACK}└─────────────────────────────────────────────────────────┘${NC}"
    sleep 0.3
    
    # Final boot message
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    sleep 0.1
    echo -e "${GREEN}  🚀 BOOT SEQUENCE COMPLETE - ACTIVATING BEAST MODE! 🔥${NC}"
    sleep 0.1
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    sleep 1
    clear
}

# Animation spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while kill -0 $pid 2>/dev/null; do
        for i in $(seq 0 9); do
            echo -ne "\r${CYAN}${spinstr:$i:1}${NC} $2 "
            sleep $delay
        done
    done
    echo -ne "\r"
}

# Progress bar animation
progress_bar() {
    local duration=$1
    local width=30
    for ((i=0; i<=width; i++)); do
        percent=$((i * 100 / width))
        bar=$(printf '█%.0s' $(seq 1 $i))
        empty=$(printf '░%.0s' $(seq 1 $((width - i))))
        echo -ne "\r${GREEN}[${bar}${empty}] ${percent}%${NC} "
        sleep $((duration / (width + 1)))
    done
    echo -ne "\r${GREEN}[$(printf '█%.0s' $(seq 1 $width))] 100%${NC}\n"
}

# Show loading screen
loading_screen

# Print banner
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🎵 TELEGRAM MUSIC BOT - TERMUX AUTO LAUNCHER 🎵        ║"
echo "║                  Running in Beast Mode 🚀                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Set Android API level
echo -e "${YELLOW}⚙️  Setting up environment...${NC}"
export ANDROID_API_LEVEL=24
sleep 1

# Update Termux packages with animation
echo -e "${BLUE}📦 Updating system packages...${NC}"
(pkg update -y 2>/dev/null &)
pid=$!
spinner $pid "Updating packages..."
wait $pid
echo -e "${GREEN}✓ Packages updated${NC}"
progress_bar 2

# Install required system packages
echo -e "${BLUE}📥 Installing system dependencies...${NC}"
pkg install python ffmpeg git python-cryptography libffi openssl -y
echo -e "${GREEN}✓ System packages installed${NC}"

# Install Python libraries
echo -e "${BLUE}📚 Installing Python libraries (this may take a minute on first run)...${NC}"
pip install "python-telegram-bot[job-queue]" yt-dlp google-genai python-dotenv requests aiofiles Pillow
echo -e "${GREEN}✓ Python libraries installed successfully${NC}"

# Ready notification
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║${GREEN}         ✅ ENVIRONMENT READY - STARTING BOT!          ${CYAN}║"
echo "║${PURPLE}             Beast Mode Activated 🔥                   ${CYAN}║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Run bot with auto-restart loop with animations
counter=0
while true
do
    counter=$((counter + 1))
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${WHITE} 🎵 BOT SESSION #$counter ${CYAN}│${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────┘${NC}"
    echo -e "${GREEN}▶ Starting bot.py${NC}"
    
    # Run bot
    python bot.py
    
    # Bot stopped - show animation
    echo -e "${RED}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║              ⚠️  BOT DISCONNECTED - RESTARTING             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${YELLOW}Reconnecting in:${NC}"
    for i in {5..1}; do
        echo -ne "\r${PURPLE}  ⏳ $i seconds...${NC}  "
        sleep 1
    done
    echo -e "\r${GREEN}  ✓ Reconnecting now!${NC}  \n"
    sleep 1
done
