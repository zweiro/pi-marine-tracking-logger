"""
Polling Scheduler Service

Manages periodic fetching of satellite data using APScheduler.
"""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.satellite_fetcher import SatelliteFetcher

logger = logging.getLogger(__name__)


class PollingScheduler:
    """
    Manages scheduled polling of satellite API.

    Usage:
        scheduler = PollingScheduler(
            db=database,
            satellite_api_url="http://mock-satellite:8001",
            interval_seconds=300,
            enabled=True,
        )
        await scheduler.start()
        # ... later
        await scheduler.stop()
    """

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        satellite_api_url: str,
        interval_seconds: int = 300,
        enabled: bool = True,
    ):
        self.db = db
        self.satellite_api_url = satellite_api_url
        self.interval_seconds = interval_seconds
        self.enabled = enabled

        self.scheduler: AsyncIOScheduler | None = None
        self.fetcher: SatelliteFetcher | None = None
        self._is_running = False

    async def _fetch_job(self):
        """Job that runs periodically to fetch and process packets."""
        if not self.fetcher:
            return

        logger.info(f"[Scheduler] Starting fetch job at {datetime.utcnow().isoformat()}")

        try:
            result = await self.fetcher.fetch_and_process()

            if result.get("success"):
                logger.info(
                    f"[Scheduler] Fetch completed: "
                    f"{result.get('packets_fetched', 0)} packets, "
                    f"{result.get('dives_created', 0)} dives created"
                )
            else:
                logger.error(f"[Scheduler] Fetch failed: {result.get('error')}")

        except Exception as e:
            logger.exception(f"[Scheduler] Unexpected error during fetch: {e}")

    async def start(self):
        """Start the scheduler."""
        if not self.enabled:
            logger.info("[Scheduler] Polling is disabled, not starting scheduler")
            return

        if self._is_running:
            logger.warning("[Scheduler] Already running")
            return

        # Initialize fetcher
        self.fetcher = SatelliteFetcher(
            db=self.db,
            satellite_api_url=self.satellite_api_url,
        )

        # Initialize scheduler
        self.scheduler = AsyncIOScheduler()

        # Add the fetch job
        self.scheduler.add_job(
            self._fetch_job,
            trigger=IntervalTrigger(seconds=self.interval_seconds),
            id="satellite_fetch",
            name="Satellite Data Fetch",
            replace_existing=True,
        )

        # Start scheduler
        self.scheduler.start()
        self._is_running = True

        logger.info(
            f"[Scheduler] Started with interval={self.interval_seconds}s, "
            f"API URL={self.satellite_api_url}"
        )

        # Run initial fetch immediately
        logger.info("[Scheduler] Running initial fetch...")
        await self._fetch_job()

    async def stop(self):
        """Stop the scheduler."""
        if self.scheduler and self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("[Scheduler] Stopped")

        if self.fetcher:
            await self.fetcher.close()
            self.fetcher = None

    async def trigger_now(self) -> dict:
        """
        Manually trigger a fetch operation.

        Returns:
            Fetch result dictionary
        """
        if not self.fetcher:
            self.fetcher = SatelliteFetcher(
                db=self.db,
                satellite_api_url=self.satellite_api_url,
            )

        return await self.fetcher.fetch_and_process()

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running

    def get_status(self) -> dict:
        """Get scheduler status."""
        next_run = None
        if self.scheduler and self._is_running:
            job = self.scheduler.get_job("satellite_fetch")
            if job and job.next_run_time:
                next_run = job.next_run_time.isoformat()

        return {
            "enabled": self.enabled,
            "running": self._is_running,
            "interval_seconds": self.interval_seconds,
            "satellite_api_url": self.satellite_api_url,
            "next_run": next_run,
        }
