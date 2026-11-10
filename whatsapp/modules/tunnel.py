"""Cloudflare Quick Tunnel Manager for WhatsApp Bot.
Provides free, secure, public HTTPS URLs (https://*.trycloudflare.com)
so users on mobile data / outside local WiFi can open video links, stream,
and download in 1080p, 720p, 480p, and MP3 without localhost restrictions.
"""

import os
import re
import sys
import time
import shutil
import atexit
import logging
import threading
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("cloudflare_tunnel")

class CloudflareTunnelManager:
    """Manages the lifecycle of a cloudflared quick tunnel."""

    DEFAULT_PATHS = [
        r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
        r"C:\Program Files\cloudflared\cloudflared.exe",
        str(Path(__file__).resolve().parent.parent / "bin" / "cloudflared.exe"),
    ]

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._tunnel_url: Optional[str] = None
        self._is_starting = False
        self._is_running = False
        self._port = 5000
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_requested = False

        # Register cleanup on program exit
        atexit.register(self.stop_tunnel)

    def find_cloudflared_executable(self) -> Optional[str]:
        """Find the cloudflared executable path on the system."""
        # 1. System PATH
        which_path = shutil.which("cloudflared")
        if which_path and os.path.isfile(which_path):
            return which_path

        # 2. Well-known install locations
        for p in self.DEFAULT_PATHS:
            if os.path.isfile(p):
                return p

        return None

    @property
    def tunnel_url(self) -> Optional[str]:
        return self._tunnel_url

    @property
    def is_running(self) -> bool:
        return self._is_running and self._process is not None and self._process.poll() is None

    def start_tunnel(self, port: int = 5000, wait_seconds: int = 15) -> Optional[str]:
        """Start cloudflared tunnel in a background thread and wait for public HTTPS URL."""
        with self._lock:
            if self.is_running and self._tunnel_url:
                logger.info(f"Cloudflare tunnel already running: {self._tunnel_url}")
                return self._tunnel_url

            self._port = port
            self._stop_requested = False
            bin_path = self.find_cloudflared_executable()
            if not bin_path:
                logger.error("cloudflared executable not found! Cloudflare tunnel cannot start.")
                return None

            logger.info(f"Starting Cloudflare Quick Tunnel using: {bin_path} -> port {port}")
            self._is_starting = True

            cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{port}"]

            try:
                # Use creationflags=subprocess.CREATE_NO_WINDOW on Windows to prevent console window popup
                creation_flags = 0
                if sys.platform == "win32":
                    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=creation_flags
                )
            except Exception as e:
                logger.error(f"Failed to spawn cloudflared process: {e}")
                self._is_starting = False
                return None

        # Wait for the tunnel URL in output
        found_url = None
        start_time = time.time()

        while time.time() - start_time < wait_seconds:
            if self._process.poll() is not None:
                logger.error("cloudflared process terminated prematurely.")
                break

            line = self._process.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue

            clean_line = line.strip()
            # Search for https://<name>.trycloudflare.com
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", clean_line)
            if match:
                found_url = match.group(0).rstrip("/")
                logger.info(f"Cloudflare Quick Tunnel created successfully: {found_url}")
                break

        if found_url:
            self._tunnel_url = found_url
            self._is_running = True
            self._is_starting = False

            # Update public_url in config_manager if available
            try:
                from modules.config import config_manager
                config_manager.update({"public_url": found_url})
            except Exception as e:
                logger.warning(f"Could not update config_manager with tunnel URL: {e}")

            # Start background reader & watchdog to keep pipes drained and restart if killed
            if not self._monitor_thread or not self._monitor_thread.is_alive():
                self._monitor_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
                self._monitor_thread.start()

            return found_url
        else:
            logger.warning("Cloudflare tunnel did not produce a trycloudflare.com URL within timeout.")
            self._is_starting = False
            return None

    def _watchdog_loop(self):
        """Continuously drains output and monitors process health."""
        while not self._stop_requested:
            if not self._process or self._process.poll() is not None:
                if self._stop_requested:
                    break
                logger.warning("Cloudflare tunnel process exited unexpectedly. Reconnecting in 5s...")
                self._is_running = False
                self._tunnel_url = None
                time.sleep(5)
                if not self._stop_requested:
                    self.start_tunnel(self._port, wait_seconds=20)
                break

            try:
                line = self._process.stdout.readline()
                if not line:
                    time.sleep(0.2)
                    continue
                match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if match:
                    new_url = match.group(0).rstrip("/")
                    if new_url != self._tunnel_url:
                        self._tunnel_url = new_url
                        try:
                            from modules.config import config_manager
                            config_manager.update({"public_url": new_url})
                        except Exception:
                            pass
            except Exception:
                time.sleep(0.5)

    def stop_tunnel(self):
        """Stop running tunnel process."""
        self._stop_requested = True
        with self._lock:
            if self._process:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=3)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
                self._process = None
            self._is_running = False
            self._tunnel_url = None
            logger.info("Cloudflare tunnel stopped.")

# Singleton instance
tunnel_manager = CloudflareTunnelManager()
