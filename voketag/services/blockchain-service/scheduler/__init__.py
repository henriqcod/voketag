from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger


def create_scheduler():
    return AsyncIOScheduler()


def run_anchor_job():
    pass
