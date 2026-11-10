#!/bin/bash
# ========================================================
# Telegram Bot 24/7 Mobile Launcher - Made by Satyam
# ========================================================

echo "========================================================"
echo "  🤖 Telegram Bot 24/7 Mobile Host"
echo "  ✨ Made with ❤️ by Satyam"
echo "========================================================"

# Keep Android CPU awake so background tasks never pause when screen turns off
if command -v termux-wake-lock &> /dev/null; then
    echo "⚡ Acquiring Termux Wake Lock for 24/7 background execution..."
    termux-wake-lock
fi

# Check and install python & ffmpeg if missing
if ! command -v python3 &> /dev/null; then
    echo "📦 Installing Python & FFmpeg (One-time setup, please wait)..."
    pkg update -y && pkg install -y python ffmpeg
fi

# Check and install pip requirements if missing
if ! python3 -c "import telegram, yt_dlp" &> /dev/null; then
    echo "📦 Installing required Python libraries from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Launch the mobile controller server on background port 8080
echo "🚀 Launching 24/7 Web App on http://localhost:8080 ..."
python3 mobile_app.py 8080 &
SERVER_PID=$!

sleep 2

# Open default mobile browser to the web app dashboard
if command -v termux-open-url &> /dev/null; then
    termux-open-url "http://localhost:8080"
elif command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8080"
fi

echo "========================================================"
echo "✅ Mobile App is running in the background!"
echo "👉 Open: http://localhost:8080 in your phone's browser"
echo "💡 You can add this page to your Home Screen as an App!"
echo "========================================================"

# Wait for server
wait $SERVER_PID

