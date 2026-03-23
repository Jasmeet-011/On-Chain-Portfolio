# backend/app/services/scheduler.py - UPDATED: Added Snapshot Job
"""
Background Scheduler for Alert System + Snapshots

Runs periodic tasks:
- Check price alerts (every 5 minutes)
- Send daily digests (once per day at 9 AM)
- Send weekly summaries (Sundays at 9 AM)
- Check milestones (every hour)
- Create daily snapshots (daily at 00:05 AM) ✨ NEW
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import asyncio

from app.services.alert_service import AlertService
from app.services.snapshot_service import SnapshotService


class AlertScheduler:
    """Manages scheduled tasks for alert system and snapshots"""
    
    def __init__(
        self,
        alert_service: AlertService,
        snapshot_service: SnapshotService = None  # ✨ NEW
    ):
        self.alert_service = alert_service
        self.snapshot_service = snapshot_service  # ✨ NEW
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Start the scheduler"""
        
        # ============================================================
        # PRICE ALERTS - Every 5 minutes
        # ============================================================
        self.scheduler.add_job(
            func=self._check_price_alerts,
            trigger=IntervalTrigger(minutes=5),
            id="check_price_alerts",
            name="Check price alerts",
            replace_existing=True
        )
        
        # ============================================================
        # DAILY DIGEST - Every day at 9:00 AM
        # ============================================================
        self.scheduler.add_job(
            func=self._send_daily_digests,
            trigger=CronTrigger(hour=9, minute=0),
            id="send_daily_digests",
            name="Send daily portfolio digests",
            replace_existing=True
        )
        
        # ============================================================
        # WEEKLY SUMMARY - Every Sunday at 9:00 AM
        # ============================================================
        self.scheduler.add_job(
            func=self._send_weekly_summaries,
            trigger=CronTrigger(day_of_week='sun', hour=9, minute=0),
            id="send_weekly_summaries",
            name="Send weekly performance summaries",
            replace_existing=True
        )
        
        # ============================================================
        # MILESTONE CHECKS - Every hour
        # ============================================================
        self.scheduler.add_job(
            func=self._check_milestones,
            trigger=IntervalTrigger(hours=1),
            id="check_milestones",
            name="Check price milestones",
            replace_existing=True
        )
        
        # ============================================================
        # SNAPSHOTS - Every 6 hours (00:05, 06:05, 12:05, 18:05 UTC)
        # Higher resolution than daily; unique index prevents duplicate slots.
        # ============================================================
        if self.snapshot_service:
            self.scheduler.add_job(
                func=self._create_daily_snapshots,
                trigger=IntervalTrigger(hours=6, start_date="2000-01-01 00:05:00"),
                id="create_snapshots",
                name="Create portfolio snapshots (every 6 h)",
                replace_existing=True
            )
            print("[SCHEDULER] ✨ Snapshot job added (every 6 h)")
        
        # Start scheduler
        self.scheduler.start()
        print("[SCHEDULER] Alert scheduler started")
        print(f"[SCHEDULER] Next price alert check: {self._get_next_run_time('check_price_alerts')}")
        print(f"[SCHEDULER] Next daily digest: {self._get_next_run_time('send_daily_digests')}")
        
        if self.snapshot_service:
            print(f"[SCHEDULER] Next snapshot creation: {self._get_next_run_time('create_snapshots')}")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("[SCHEDULER] Scheduler stopped")
    
    def _get_next_run_time(self, job_id: str) -> str:
        """Get next run time for a job"""
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        return "Unknown"
    
    # ============================================================
    # JOB FUNCTIONS
    # ============================================================
    
    async def _check_price_alerts(self):
        """Check all price alerts (every 5 minutes)"""
        try:
            print(f"\n[SCHEDULER] [{datetime.now()}] Checking price alerts...")
            triggered = await self.alert_service.check_all_alerts()
            print(f"[SCHEDULER] Price alert check complete. {triggered} alerts triggered.\n")
        except Exception as e:
            print(f"[SCHEDULER] Error checking alerts: {e}")
    
    async def _send_daily_digests(self):
        """Send daily portfolio digests (9 AM daily)"""
        try:
            print(f"\n[SCHEDULER] [{datetime.now()}] Sending daily digests...")
            sent = await self.alert_service.send_daily_digests()
            print(f"[SCHEDULER] Daily digests sent: {sent}\n")
        except Exception as e:
            print(f"[SCHEDULER] Error sending daily digests: {e}")
    
    async def _send_weekly_summaries(self):
        """Send weekly performance summaries (9 AM Sundays)"""
        try:
            print(f"\n[SCHEDULER] [{datetime.now()}] Sending weekly summaries...")
            sent = await self.alert_service.send_weekly_summaries()
            print(f"[SCHEDULER] Weekly summaries sent: {sent}\n")
        except Exception as e:
            print(f"[SCHEDULER] Error sending weekly summaries: {e}")
    
    async def _check_milestones(self):
        """Check for price milestones (hourly)"""
        try:
            print(f"\n[SCHEDULER] [{datetime.now()}] Checking milestones...")
            await self.alert_service.check_milestones()
            print(f"[SCHEDULER] Milestone check complete.\n")
        except Exception as e:
            print(f"[SCHEDULER] Error checking milestones: {e}")
    
    async def _create_daily_snapshots(self):
        """Create daily snapshots for all users (00:05 AM daily)"""
        try:
            print(f"\n[SCHEDULER] [{datetime.now()}] Creating daily snapshots...")
            created = await self.snapshot_service.save_all_user_snapshots()
            print(f"[SCHEDULER] Daily snapshots complete. {created} snapshots created.\n")
        except Exception as e:
            print(f"[SCHEDULER] Error creating snapshots: {e}")


# ============================================================
# MANUAL TRIGGER FUNCTIONS (for testing)
# ============================================================

async def trigger_price_check_now(alert_service: AlertService):
    """Manually trigger price alert check (for testing)"""
    print("[MANUAL] Triggering price alert check...")
    await alert_service.check_all_alerts()


async def trigger_daily_digest_now(alert_service: AlertService):
    """Manually trigger daily digest (for testing)"""
    print("[MANUAL] Triggering daily digest...")
    await alert_service.send_daily_digests()


async def trigger_weekly_summary_now(alert_service: AlertService):
    """Manually trigger weekly summary (for testing)"""
    print("[MANUAL] Triggering weekly summary...")
    await alert_service.send_weekly_summaries()


async def trigger_snapshot_now(snapshot_service: SnapshotService):
    """Manually trigger snapshot creation (for testing)"""
    print("[MANUAL] Triggering snapshot creation...")
    await snapshot_service.save_all_user_snapshots()