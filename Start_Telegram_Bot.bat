@echo off
title Telegram Bot 24/7 Host - Made by Satyam
color 0B
cd /d "%~dp0"
echo ========================================================
echo   Telegram Bot 24/7 Controller - Made by Satyam
echo ========================================================
echo Checking and installing bot dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Dependency installation failed. Check your internet connection and Python installation.
    pause
    exit /b 1
)
echo Starting GUI Dashboard...
start "" pythonw gui_app.py
exit
