"""
Discord Screenshot Bot
Captures specific windows silently and posts them to Discord.
Runs on a schedule and responds to /screenshot slash commands.
"""

import os
import sys
import json
import time
import logging
import threading
import io
from datetime import datetime
from pathlib import Path

import requests
import schedule
import discord
from discord import app_commands

# ── Windows-only imports ──────────────────────────────────────────────────────
if sys.platform != "win32":
    print("ERROR: This script requires Windows (win32gui/win32ui/win32con).")
    sys.exit(1)

import win32gui
import win32ui
import win32con
import win32api
import ctypes
from PIL import Image


# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        log.error("config.json not found next to main.py")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Screenshot capture ────────────────────────────────────────────────────────

def find_window(title: str) -> int | None:
    """Return the first HWND whose title contains `title` (case-insensitive)."""
    title_lower = title.lower()
    found = []

    def _cb(hwnd, _):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
            wnd_title = win32gui.GetWindowText(hwnd).lower()
            if title_lower in wnd_title:
                found.append(hwnd)

    win32gui.EnumWindows(_cb, None)
    return found[0] if found else None


def restore_if_minimized(hwnd: int) -> bool:
    """
    If the window is minimized, restore it briefly so PrintWindow can render it.
    Returns True if we had to restore it (so caller can re-minimize afterwards).
    """
    placement = win32gui.GetWindowPlacement(hwnd)
    # placement[1] is showCmd; SW_SHOWMINIMIZED == 2
    if placement[1] == win32con.SW_SHOWMINIMIZED:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.3)  # give the window a moment to repaint
        return True
    return False


def _get_physical_rect(hwnd: int) -> tuple[int, int, int, int]:
    """Return window rect in physical (DPI-aware) pixels."""
    # DwmGetWindowAttribute DWMWA_EXTENDED_FRAME_BOUNDS gives true physical rect
    try:
        import ctypes.wintypes
        rect = ctypes.wintypes.RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            hwnd, DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(rect), ctypes.sizeof(rect)
        )
        return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        return win32gui.GetWindowRect(hwnd)


def capture_window(hwnd: int) -> Image.Image | None:
    """
    Capture a window by grabbing the screen region it occupies via BitBlt.
    Works correctly with DPI scaling and hardware-accelerated windows (Chrome, etc).
    """
    try:
        left, top, right, bottom = _get_physical_rect(hwnd)
        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
            log.warning("Window has zero dimensions (hwnd=%d)", hwnd)
            return None

        # Capture from the screen DC (captures exactly what is visible on screen)
        screen_dc = win32gui.GetDC(0)
        mfc_dc = win32ui.CreateDCFromHandle(screen_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bmp)

        # BitBlt copies the screen region directly — full resolution, DPI-correct
        save_dc.BitBlt((0, 0), (width, height), mfc_dc, (left, top), win32con.SRCCOPY)

        bmp_info = bmp.GetInfo()
        bmp_bits = bmp.GetBitmapBits(True)

        img = Image.frombuffer(
            "RGB",
            (bmp_info["bmWidth"], bmp_info["bmHeight"]),
            bmp_bits,
            "raw",
            "BGRX",
            0,
            1,
        )

        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(0, screen_dc)
        win32gui.DeleteObject(bmp.GetHandle())

        return img

    except Exception as exc:
        log.error("GDI capture failed for hwnd=%d: %s", hwnd, exc)
        return None


def screenshot_window(title: str, quality: int = 95) -> tuple[bytes | None, str]:
    """
    Locate window by title, capture it, return (jpeg_bytes, status_message).
    """
    hwnd = find_window(title)
    if hwnd is None:
        msg = f"Window not found: '{title}'"
        log.warning(msg)
        return None, msg

    had_to_restore = restore_if_minimized(hwnd)

    img = capture_window(hwnd)

    if had_to_restore:
        # Re-minimise so the user doesn't notice
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

    if img is None:
        msg = f"Capture failed for '{title}'"
        log.error(msg)
        return None, msg

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return buf.read(), f"Captured '{title}' ({img.width}x{img.height})"


# ── Discord webhook posting ───────────────────────────────────────────────────

def post_to_webhook(
    webhook_url: str,
    image_bytes: bytes,
    filename: str,
    caption: str = "",
) -> bool:
    """POST a single image to a Discord webhook. Returns True on success."""
    try:
        resp = requests.post(
            webhook_url,
            data={"content": caption} if caption else {},
            files={"file": (filename, image_bytes, "image/jpeg")},
            timeout=30,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        log.error("Webhook post failed: %s", exc)
        return False


def capture_and_post_all(cfg: dict, *, source: str = "schedule") -> list[str]:
    """
    Capture every configured window and post to webhook.
    Returns a list of result messages (one per window).
    """
    results = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if cfg.get("include_timestamp") else ""
    prefix = f"[{ts}] " if ts else ""

    for title in cfg["window_titles"]:
        img_bytes, status = screenshot_window(title, cfg.get("screenshot_quality", 95))

        if img_bytes is None:
            results.append(f"{prefix}**{title}**: {status}")
            continue

        safe_title = "".join(c if c.isalnum() else "_" for c in title)
        filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        caption = f"{prefix}**{title}** (via {source})"

        ok = post_to_webhook(cfg["discord_webhook_url"], img_bytes, filename, caption)
        if ok:
            log.info("Posted screenshot for '%s' (%s)", title, source)
            results.append(f"{prefix}**{title}**: posted successfully")
        else:
            results.append(f"{prefix}**{title}**: webhook post failed")

    return results


# ── Discord bot ───────────────────────────────────────────────────────────────

class ScreenshotBot(discord.Client):
    def __init__(self, cfg: dict):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.cfg = cfg
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Register /screenshot command
        @self.tree.command(name="screenshot", description="Capture configured windows and post to Discord")
        async def screenshot_cmd(interaction: discord.Interaction):
            await interaction.response.defer(thinking=True)
            # Run blocking capture in a thread so we don't block the event loop
            loop = interaction.client.loop
            results = await loop.run_in_executor(
                None, lambda: capture_and_post_all(self.cfg, source="/screenshot command")
            )
            summary = "\n".join(results) if results else "No windows configured."
            await interaction.followup.send(summary)

        guild_id = self.cfg.get("command_guild_id")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info("Slash commands synced to guild %s", guild_id)
        else:
            await self.tree.sync()
            log.info("Slash commands synced globally (may take up to 1 hour to propagate)")

    async def on_ready(self):
        log.info("Bot logged in as %s (id=%d)", self.user, self.user.id)


# ── Scheduler thread ──────────────────────────────────────────────────────────

def run_scheduler(cfg: dict):
    interval = cfg.get("schedule_interval_minutes", 5)
    log.info("Scheduler started — capturing every %d minute(s)", interval)

    schedule.every(interval).minutes.do(capture_and_post_all, cfg=cfg, source="schedule")

    while True:
        schedule.run_pending()
        time.sleep(10)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    cfg = load_config()

    webhook = cfg.get("discord_webhook_url", "")
    bot_token = cfg.get("discord_bot_token", "")

    if "YOUR_WEBHOOK" in webhook or not webhook:
        log.error("Set discord_webhook_url in config.json before running.")
        sys.exit(1)

    # Start scheduler in a background daemon thread
    sched_thread = threading.Thread(target=run_scheduler, args=(cfg,), daemon=True)
    sched_thread.start()

    # Run an immediate capture on startup so the user sees it's working
    log.info("Running initial capture on startup…")
    capture_and_post_all(cfg, source="startup")

    if "YOUR_BOT_TOKEN" in bot_token or not bot_token:
        log.warning(
            "discord_bot_token not set — /screenshot command disabled. "
            "Scheduled captures will still run."
        )
        # Keep the process alive for the scheduler
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            log.info("Shutting down.")
        return

    bot = ScreenshotBot(cfg)
    try:
        bot.run(bot_token, log_handler=None)  # discord.py has its own logging
    except discord.LoginFailure:
        log.error("Invalid bot token. Check discord_bot_token in config.json.")
        sys.exit(1)
    except KeyboardInterrupt:
        log.info("Shutting down.")


if __name__ == "__main__":
    main()
