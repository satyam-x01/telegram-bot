#!/data/data/com.termux/files/usr/bin/bash
if [ -f bot.log ]; then
    echo "📜 --- Bot Recent Logs ---"
    tail -n 25 bot.log
else
    echo "⚠️ bot.log file abhi nahi bani hai. Pehle 'bash start.sh' chalayein."
fi
