"""
Discord Screenshot Bot — entry point
"""

import sys
import json
import logging
import threading
import time
from pathlib import Path

import discord

from bot.scheduler import run_scheduler
from bot.webhook import capture_and_post_all
from bot.discord_bot import ScreenshotBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        log.error("config.json not found.")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    if sys.platform != "win32":
        log.error("This bot requires Windows.")
        sys.exit(1)

    cfg = load_config()

    webhook = cfg.get("discord_webhook_url", "")
    bot_token = cfg.get("discord_bot_token", "")

    if not webhook or "YOUR_WEBHOOK" in webhook:
        log.error("Set discord_webhook_url in config.json before running.")
        sys.exit(1)

    threading.Thread(target=run_scheduler, args=(cfg,), daemon=True).start()

    log.info("Running initial capture on startup...")
    capture_and_post_all(cfg, source="startup")

    if not bot_token or "YOUR_BOT_TOKEN" in bot_token:
        log.warning("discord_bot_token not set — /screenshot command disabled.")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            log.info("Shutting down.")
        return

    bot = ScreenshotBot(cfg)
    try:
        bot.run(bot_token, log_handler=None)
    except discord.LoginFailure:
        log.error("Invalid bot token. Check discord_bot_token in config.json.")
        sys.exit(1)
    except KeyboardInterrupt:
        log.info("Shutting down.")


if __name__ == "__main__":
    main()
