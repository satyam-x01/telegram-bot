#!/data/data/com.termux/files/usr/bin/bash
# ========================================================
# Satyam WhatsApp Bot - Native Termux Setup (No Ubuntu needed!)
# ========================================================

set -e

echo "📦 [1/3] Updating Termux..."
pkg update -y

echo "🔧 [2/3] Installing Python, Cryptography, Pillow, and build tools..."
pkg install -y python python-cryptography python-pillow python-cffi ffmpeg git clang libjpeg-turbo libpng make binutils openssl

echo "📥 [3/3] Installing Python libraries (neonize, flask, etc.)..."
pip install --upgrade setuptools wheel
pip install -r requirements.txt

echo "========================================================"
echo "✅ Native Termux Setup Completed Successfully!"
echo "========================================================"
echo "Bot ko chalane ke liye:"
echo "   python run.py        (Normal test)"
echo "   bash start.sh        (Background me 24/7 chalane ke liye)"
echo "========================================================"
