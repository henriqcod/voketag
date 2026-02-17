import logging
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import get_settings
from scheduler.runner import run_anchor_cycle

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("blockchain-service")


def main():
    settings = get_settings()
    scheduler = BlockingScheduler()

    scheduler.add_job(
        run_anchor_cycle,
        IntervalTrigger(minutes=1),
        id="anchor_cycle",
        replace_existing=True,
    )

    def shutdown(signum=None, frame=None):
        logger.info("shutdown signal received")
        scheduler.shutdown(wait=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info("scheduler starting (interval=1min)")
    scheduler.start()


if __name__ == "__main__":
    main()
