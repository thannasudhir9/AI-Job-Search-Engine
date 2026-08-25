from apscheduler.schedulers.background import BackgroundScheduler

from ..config import SYNC_INTERVAL_HOURS

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler | None:
    return _scheduler


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _run_sync,
        "interval",
        hours=SYNC_INTERVAL_HOURS,
        id="board_sync",
        next_run_time=None,  # first sync happens on startup hook instead
    )
    _scheduler.start()
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def _run_sync():
    from ..db import SessionLocal
    from .sync import sync_all

    db = SessionLocal()
    try:
        sync_all(db)
    finally:
        db.close()
