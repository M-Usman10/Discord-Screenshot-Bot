import time
import logging

import schedule

from bot.webhook import capture_and_post_all

log = logging.getLogger(__name__)


def run_scheduler(cfg: dict) -> None:
    """Block forever, firing capture_and_post_all on the configured interval."""
    interval = cfg.get("schedule_interval_minutes", 5)
    log.info("Scheduler started — capturing every %d minute(s)", interval)

    schedule.every(interval).minutes.do(capture_and_post_all, cfg=cfg, source="schedule")

    while True:
        schedule.run_pending()
        time.sleep(10)
