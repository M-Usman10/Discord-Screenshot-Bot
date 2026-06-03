import sys
import io
import time
import ctypes
import logging

if sys.platform != "win32":
    raise RuntimeError("capture.py requires Windows.")

import win32gui
import win32ui
import win32con
from PIL import Image

# DPI-aware so GetWindowRect returns physical pixels
ctypes.windll.shcore.SetProcessDpiAwareness(2)

log = logging.getLogger(__name__)

PW_RENDERFULLCONTENT = 2


def find_windows(title: str) -> list[int]:
    """Return all visible HWNDs whose title contains `title` (case-insensitive)."""
    title_lower = title.lower()
    found: list[int] = []

    def _cb(hwnd: int, _) -> None:
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
            if title_lower in win32gui.GetWindowText(hwnd).lower():
                found.append(hwnd)

    win32gui.EnumWindows(_cb, None)
    return found


def _restore_if_minimized(hwnd: int) -> bool:
    """Restore minimized window so PrintWindow can render it. Returns True if restored."""
    if win32gui.GetWindowPlacement(hwnd)[1] == win32con.SW_SHOWMINIMIZED:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.3)
        return True
    return False


def _capture_hwnd(hwnd: int) -> Image.Image | None:
    """Capture a single window via PrintWindow. Returns PIL Image or None on failure."""
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width, height = right - left, bottom - top

        if width <= 0 or height <= 0:
            log.warning("Window hwnd=%d has zero dimensions", hwnd)
            return None

        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bmp)

        result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), PW_RENDERFULLCONTENT)
        if not result:
            ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 0)

        bmp_info = bmp.GetInfo()
        bmp_bits = bmp.GetBitmapBits(True)

        img = Image.frombuffer(
            "RGB",
            (bmp_info["bmWidth"], bmp_info["bmHeight"]),
            bmp_bits, "raw", "BGRX", 0, 1,
        )

        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)
        win32gui.DeleteObject(bmp.GetHandle())

        return img

    except Exception as exc:
        log.error("GDI capture failed for hwnd=%d: %s", hwnd, exc)
        return None


def screenshot_window(title: str, quality: int = 95) -> list[tuple[bytes | None, str]]:
    """
    Capture all windows matching `title`.
    Returns list of (jpeg_bytes, status_message) — one entry per matched window.
    """
    hwnds = find_windows(title)
    if not hwnds:
        msg = f"Window not found: '{title}'"
        log.warning(msg)
        return [(None, msg)]

    results: list[tuple[bytes | None, str]] = []
    for hwnd in hwnds:
        label = win32gui.GetWindowText(hwnd)
        restored = _restore_if_minimized(hwnd)
        img = _capture_hwnd(hwnd)
        if restored:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

        if img is None:
            results.append((None, f"Capture failed for '{label}'"))
            continue

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        buf.seek(0)
        results.append((buf.read(), f"Captured '{label}' ({img.width}x{img.height})"))

    return results
