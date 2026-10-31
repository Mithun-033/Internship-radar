"""
Background Scheduler.
Manages automatic periodic source polling, catch-up after sleep/restart,
and Asia/Kolkata daily midnight rollover.
"""
import threading
import time
import datetime
import logging
from typing import Optional

from .config import APP_TIMEZONE, DEFAULT_CHECK_INTERVAL_MINUTES
from .collector import pipeline
from .database import update_daily_flags

logger = logging.getLogger("internship_radar.scheduler")

class BackgroundScheduler:
    def __init__(self, interval_minutes: int = DEFAULT_CHECK_INTERVAL_MINUTES):
        self.interval_minutes = interval_minutes
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_run_time: Optional[datetime.datetime] = None
        self.next_run_time: Optional[datetime.datetime] = None
        self.last_rollover_date: Optional[str] = None

    def start(self):
        """Starts the background worker thread."""
        if self.running:
            logger.info("Scheduler already running.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True, name="RadarSchedulerThread")
        self.thread.start()
        logger.info(f"Background scheduler started with interval {self.interval_minutes}m.")

    def stop(self):
        """Gracefully signals the worker thread to stop."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        logger.info("Background scheduler stopped.")

    def trigger_immediate_refresh(self):
        """Triggers an out-of-band immediate collection in a separate thread."""
        t = threading.Thread(target=self._run_cycle, daemon=True, name="ManualRefreshThread")
        t.start()
        return t

    def _run_cycle(self):
        """Executes a single collection cycle and calculates next run time."""
        now_ist = datetime.datetime.now(APP_TIMEZONE)
        today_ist_str = now_ist.strftime("%Y-%m-%d")

        # Check for date rollover
        if self.last_rollover_date != today_ist_str:
            logger.info(f"Day rollover detected: Updating daily feed flags to {today_ist_str} (Asia/Kolkata)...")
            update_daily_flags(today_ist_str)
            self.last_rollover_date = today_ist_str

        self.last_run_time = now_ist
        self.next_run_time = now_ist + datetime.timedelta(minutes=self.interval_minutes)

        try:
            res = pipeline.run_all()
            logger.info(f"Scheduler cycle finished: {res}")
        except Exception as e:
            logger.error(f"Error during scheduler run: {e}", exc_info=True)

    def _loop(self):
        """Main periodic loop."""
        # Initial cycle on startup (catch-up / backfill)
        logger.info("Performing startup catch-up collection...")
        self._run_cycle()

        while self.running:
            # Sleep in small increments to allow responsive shutdown
            now_ist = datetime.datetime.now(APP_TIMEZONE)
            
            # Check rollover every loop
            today_ist_str = now_ist.strftime("%Y-%m-%d")
            if self.last_rollover_date != today_ist_str:
                logger.info(f"Midnight rollover detected. Updating feed for {today_ist_str}...")
                update_daily_flags(today_ist_str)
                self.last_rollover_date = today_ist_str

            # Check if next_run_time has passed (handles waking from laptop sleep)
            if self.next_run_time and now_ist >= self.next_run_time:
                logger.info(f"Scheduled time reached ({now_ist.strftime('%H:%M:%S')}). Running periodic check...")
                self._run_cycle()

            for _ in range(10):
                if not self.running:
                    break
                time.sleep(1.0)

    def get_status(self):
        """Returns scheduler state for the frontend overview."""
        now_ist = datetime.datetime.now(APP_TIMEZONE)
        return {
            "running": self.running,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run_time.strftime("%Y-%m-%d %H:%M:%S %Z") if self.last_run_time else None,
            "next_run": self.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z") if self.next_run_time else None,
            "current_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S %Z")
        }

scheduler = BackgroundScheduler()
