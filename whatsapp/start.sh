#!/data/data/com.termux/files/usr/bin/bash
# Enable wake lock so CPU stays awake
termux-wake-lock 2>/dev/null || true

# Kill existing instance if running
pkill -f "python run.py" 2>/dev/null || true

# Start bot in background
nohup python run.py > bot.log 2>&1 &

echo "================================================="
echo "🚀 WhatsApp Bot background me START ho gaya hai!"
echo "================================================="
echo "• Logs dekhne ke liye: bash status.sh"
echo "• Bot band karne ke liye: bash stop.sh"
echo "• Dashboard URL: http://localhost:5000"
echo "================================================="
