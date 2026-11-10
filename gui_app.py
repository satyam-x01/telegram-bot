#!/usr/bin/env python3
"""
Telegram Bot 24/7 Desktop GUI Controller
========================================
Made by Satyam

Standalone native desktop controller to run the Telegram Bot 24/7
with live console monitoring, token management, and secret protection.
"""

import os
import sys
import json
import time
import queue
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

BASE_DIR = Path(__file__).parent.resolve()
CRED_FILE = BASE_DIR / ".bot_credentials.json"
BOT_SCRIPT = BASE_DIR / "bot.py"


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


class TelegramBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Bot 24/7 Host — Made by Satyam")
        self.root.geometry("640x720")
        self.root.minsize(540, 600)
        self.root.configure(bg="#0b0f19")

        self.bot_process = None
        self.log_queue = queue.Queue()

        self._setup_styles()
        self._build_ui()
        self._load_initial_data()
        self._check_log_queue()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

    def _build_ui(self):
        # ─── HEADER ───
        header_frame = tk.Frame(self.root, bg="#141a2b", padx=20, pady=16, highlightthickness=1, highlightbackground="#1e293b")
        header_frame.pack(fill="x", padx=16, pady=(16, 10))

        title_lbl = tk.Label(
            header_frame,
            text="🤖 Telegram Bot 24/7",
            font=("Segoe UI", 18, "bold"),
            fg="#f8fafc",
            bg="#141a2b"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header_frame,
            text="Protected Academic Study & NASA System",
            font=("Segoe UI", 10),
            fg="#94a3b8",
            bg="#141a2b"
        )
        sub_lbl.pack(anchor="w", pady=(2, 8))

        self.status_lbl = tk.Label(
            header_frame,
            text="🔴 Status: Stopped",
            font=("Segoe UI", 11, "bold"),
            fg="#ef4444",
            bg="#1e1822",
            padx=12,
            pady=4
        )
        self.status_lbl.pack(anchor="w")

        # ─── CREDENTIALS CARD ───
        cred_frame = tk.Frame(self.root, bg="#141a2b", padx=20, pady=14, highlightthickness=1, highlightbackground="#1e293b")
        cred_frame.pack(fill="x", padx=16, pady=8)

        card_title = tk.Label(
            cred_frame,
            text="🔑 Bot Credentials",
            font=("Segoe UI", 12, "bold"),
            fg="#38bdf8",
            bg="#141a2b"
        )
        card_title.pack(anchor="w", pady=(0, 10))

        # Bot Token
        tk.Label(cred_frame, text="Telegram Bot Token:", font=("Segoe UI", 9, "bold"), fg="#94a3b8", bg="#141a2b").pack(anchor="w")
        token_row = tk.Frame(cred_frame, bg="#141a2b")
        token_row.pack(fill="x", pady=(3, 10))
        self.token_entry = tk.Entry(token_row, font=("Segoe UI", 10), bg="#060911", fg="#f8fafc", insertbackground="#38bdf8", relief="flat", show="•")
        self.token_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        self.show_token_btn = tk.Button(token_row, text="👁", font=("Segoe UI", 9), bg="#1e293b", fg="#94a3b8", relief="flat", command=self.toggle_token_visibility)
        self.show_token_btn.pack(side="right", ipady=2, ipadx=6)

        # Gemini API Key
        tk.Label(cred_frame, text="Gemini AI API Key:", font=("Segoe UI", 9, "bold"), fg="#94a3b8", bg="#141a2b").pack(anchor="w")
        gemini_row = tk.Frame(cred_frame, bg="#141a2b")
        gemini_row.pack(fill="x", pady=(3, 10))
        self.gemini_entry = tk.Entry(gemini_row, font=("Segoe UI", 10), bg="#060911", fg="#f8fafc", insertbackground="#38bdf8", relief="flat", show="•")
        self.gemini_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        self.show_gemini_btn = tk.Button(gemini_row, text="👁", font=("Segoe UI", 9), bg="#1e293b", fg="#94a3b8", relief="flat", command=self.toggle_gemini_visibility)
        self.show_gemini_btn.pack(side="right", ipady=2, ipadx=6)

        save_btn = tk.Button(
            cred_frame,
            text="💾 Save Credentials",
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b",
            fg="#38bdf8",
            relief="flat",
            cursor="hand2",
            command=self.save_creds
        )
        save_btn.pack(anchor="e", ipady=4, ipadx=12)

        # ─── ACTION BUTTON ───
        action_frame = tk.Frame(self.root, bg="#0b0f19")
        action_frame.pack(fill="x", padx=16, pady=8)

        self.start_btn = tk.Button(
            action_frame,
            text="🚀 START BOT (24/7)",
            font=("Segoe UI", 13, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            command=self.toggle_bot
        )
        self.start_btn.pack(fill="x", ipady=10)

        # ─── LIVE CONSOLE LOGS ───
        log_frame = tk.Frame(self.root, bg="#141a2b", padx=16, pady=12, highlightthickness=1, highlightbackground="#1e293b")
        log_frame.pack(fill="both", expand=True, padx=16, pady=8)

        tk.Label(log_frame, text="📋 Live Console Logs", font=("Segoe UI", 11, "bold"), fg="#38bdf8", bg="#141a2b").pack(anchor="w", pady=(0, 6))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap="word",
            font=("Consolas", 9),
            bg="#060911",
            fg="#38bdf8",
            insertbackground="#38bdf8",
            relief="flat",
            height=8
        )
        self.log_text.pack(fill="both", expand=True)

        # ─── FOOTER: MADE BY SATYAM ───
        footer_frame = tk.Frame(self.root, bg="#0b0f19", pady=10)
        footer_frame.pack(fill="x", side="bottom")

        satyam_lbl = tk.Label(
            footer_frame,
            text="✨ Made with ❤️ by Satyam ✨",
            font=("Segoe UI", 11, "bold"),
            fg="#c084fc",
            bg="#0b0f19"
        )
        satyam_lbl.pack()

    def _load_initial_data(self):
        creds = load_credentials()
        if creds.get("bot_token"):
            self.token_entry.insert(0, creds["bot_token"])
        if creds.get("gemini_api_key"):
            self.gemini_entry.insert(0, creds["gemini_api_key"])

    def toggle_token_visibility(self):
        if self.token_entry.cget("show") == "":
            self.token_entry.config(show="•")
        else:
            self.token_entry.config(show="")

    def toggle_gemini_visibility(self):
        if self.gemini_entry.cget("show") == "":
            self.gemini_entry.config(show="•")
        else:
            self.gemini_entry.config(show="")

    def save_creds(self):
        token = self.token_entry.get().strip()
        gemini = self.gemini_entry.get().strip()
        save_credentials(token, gemini)
        messagebox.showinfo("Saved", "Bot Credentials successfully saved!")

    def append_log(self, text: str):
        self.log_queue.put(text)

    def _check_log_queue(self):
        while not self.log_queue.empty():
            line = self.log_queue.get_nowait()
            self.log_text.insert(tk.END, line + "\n")
            self.log_text.see(tk.END)
        self.root.after(100, self._check_log_queue)

    def toggle_bot(self):
        if self.bot_process and self.bot_process.poll() is None:
            self.stop_bot()
        else:
            self.start_bot()

    def start_bot(self):
        token = self.token_entry.get().strip()
        gemini = self.gemini_entry.get().strip()

        if not token:
            messagebox.showerror("Error", "Please enter your Telegram Bot Token!")
            return

        save_credentials(token, gemini)

        env = os.environ.copy()
        env["TELEGRAM_BOT_TOKEN"] = token
        if gemini:
            env["GEMINI_API_KEY"] = gemini
        env["PYTHONUNBUFFERED"] = "1"

        self.append_log(f"[{time.strftime('%H:%M:%S')}] 🚀 Starting 24/7 Telegram Bot process...")

        cmd = [sys.executable, str(BOT_SCRIPT)]
        try:
            self.bot_process = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        except Exception as e:
            self.append_log(f"❌ Failed to start bot: {e}")
            messagebox.showerror("Startup Error", str(e))
            return

        # UI Update
        self.status_lbl.config(text="🟢 Status: Online 24/7", fg="#22c55e", bg="#152418")
        self.start_btn.config(text="⏹ STOP BOT", bg="#dc2626", activebackground="#b91c1c")

        # Start Log Reader Thread
        t = threading.Thread(target=self._read_process_output, daemon=True)
        t.start()

    def _read_process_output(self):
        proc = self.bot_process
        if not proc:
            return
        try:
            for line in iter(proc.stdout.readline, ''):
                if not line:
                    break
                self.append_log(line.strip())
        except Exception:
            pass

        # If process exited
        self.root.after(0, self._handle_process_exit)

    def _handle_process_exit(self):
        if self.bot_process and self.bot_process.poll() is not None:
            self.append_log(f"[{time.strftime('%H:%M:%S')}] 🔴 Bot process stopped.")
            self.status_lbl.config(text="🔴 Status: Stopped", fg="#ef4444", bg="#1e1822")
            self.start_btn.config(text="🚀 START BOT (24/7)", bg="#0284c7", activebackground="#0369a1")
            self.bot_process = None

    def stop_bot(self):
        if self.bot_process and self.bot_process.poll() is None:
            self.append_log(f"[{time.strftime('%H:%M:%S')}] ⏹ Terminating Bot Process...")
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=4)
            except Exception:
                try:
                    self.bot_process.kill()
                except Exception:
                    pass
        self._handle_process_exit()

    def on_close(self):
        if self.bot_process and self.bot_process.poll() is None:
            if messagebox.askyesno("Exit Confirmation", "The Telegram Bot is currently running 24/7.\\nDo you want to stop the bot and exit?"):
                self.stop_bot()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = TelegramBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
