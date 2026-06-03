import logging
import warnings
from datetime import datetime

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

from bot.capture import screenshot_window

log = logging.getLogger(__name__)


def post_to_webhook(
    webhook_url: str,
    image_bytes: bytes,
    filename: str,
    caption: str = "",
) -> bool:
    """POST a single JPEG image to a Discord webhook. Returns True on success."""
    try:
        resp = requests.post(
            webhook_url,
            data={"content": caption} if caption else {},
            files={"file": (filename, image_bytes, "image/jpeg")},
            timeout=30,
            verify=False,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        log.error("Webhook post failed: %s", exc)
        return False


def capture_and_post_all(cfg: dict, *, source: str = "schedule") -> list[str]:
    """
    Capture every configured window and post screenshots to the webhook.
    Returns a list of human-readable result messages.
    """
    results: list[str] = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if cfg.get("include_timestamp") else ""
    prefix = f"[{ts}] " if ts else ""

    for title in cfg["window_titles"]:
        captures = screenshot_window(title, cfg.get("screenshot_quality", 95))

        for idx, (img_bytes, status) in enumerate(captures):
            if img_bytes is None:
                results.append(f"{prefix}**{title}**: {status}")
                continue

            safe_title = "".join(c if c.isalnum() else "_" for c in title)
            suffix = f"_{idx + 1}" if len(captures) > 1 else ""
            filename = f"{safe_title}{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            caption = f"{prefix}**{status}** (via {source})"

            ok = post_to_webhook(cfg["discord_webhook_url"], img_bytes, filename, caption)
            if ok:
                log.info("Posted: %s (%s)", status, source)
                results.append(f"{prefix}{status}: posted successfully")
            else:
                results.append(f"{prefix}{status}: webhook post failed")

    return results
