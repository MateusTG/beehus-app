import logging
from celery.beat import Scheduler, ScheduleEntry
from celery import current_app
from core.models.mongo_models import Job
from core.db import init_db
import asyncio
from celery.schedules import crontab
from datetime import datetime

logger = logging.getLogger(__name__)

class MongoScheduleEntry(ScheduleEntry):
    def __init__(self, name, task, last_run_at=None, total_run_count=None,
                 schedule=None, args=(), kwargs=None, options=None,
                 relative=False, app=None):
        super().__init__(name, task, last_run_at, total_run_count,
                         schedule, args, kwargs, options, relative, app)

class MongoScheduler(Scheduler):
    Entry = MongoScheduleEntry
    
    # Sync with MongoDB every 60 seconds
    max_interval = 60

    def __init__(self, *args, **kwargs):
        self._schedule = {}
        super().__init__(*args, **kwargs)

    def setup_schedule(self):
        """Initialize schedule from MongoDB"""
        self.install_default_entries(self._schedule)
        self.sync_from_db()

    def sync_from_db(self):
        """Sync schedule from MongoDB"""
        logger.info("🔄 Syncing Celery Beat schedule from MongoDB...")
        try:
            # Run async DB code in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            new_schedule = loop.run_until_complete(self._get_jobs_from_db())
            loop.close()

            # Remove jobs that no longer exist in DB
            current_job_keys = set(self._schedule.keys())
            new_job_keys = set(new_schedule.keys())
            
            removed_jobs = current_job_keys - new_job_keys - {'celery.backend_cleanup'}
            for job_key in removed_jobs:
                logger.info(f"🗑️  Removing deleted job: {job_key}")
                self._schedule.pop(job_key, None)
            
            # Update schedule with new/modified jobs
            self.merge_inplace(new_schedule)
            
            logger.info(f"✅ Synced {len(new_schedule)} periodic jobs (removed {len(removed_jobs)})")
        except Exception as e:
            logger.error(f"❌ Failed to sync schedule: {e}")

    async def _get_jobs_from_db(self):
        try:
            await init_db()
            logger.info("🔍 Querying MongoDB for scheduled jobs...")
            
            # Query for scheduled jobs
            jobs = await Job.find(
                Job.status == "active",
                Job.schedule != None,
                Job.schedule != ""
            ).to_list()
            
            logger.info(f"📅 Found {len(jobs)} scheduled jobs")

            schedule = {}
            for job in jobs:
                try:
                    # Parse cron: "minute hour day month day_of_week"
                    parts = job.schedule.split()
                    if len(parts) == 5:
                        schedule[f'job-{job.id}'] = self.Entry(
                            name=f'job-{job.id}',
                            app=self.app,
                            task='core.tasks.scheduled_job_runner',
                            schedule=crontab(
                                minute=parts[0],
                                hour=parts[1],
                                day_of_month=parts[2],
                                month_of_year=parts[3],
                                day_of_week=parts[4]
                            ),
                            args=(str(job.id),)
                        )
                        logger.info(f"✅ Scheduled job-{job.id} with cron: {job.schedule}")
                    else:
                        logger.warning(f"⚠️  Invalid cron format for job {job.id}: {job.schedule}")
                except Exception as ex:
                    logger.error(f"❌ Failed to parse schedule for job {job.id}: {ex}")
            
            return schedule
        except Exception as e:
            logger.error(f"💥 Exception in _get_jobs_from_db: {e}", exc_info=True)
            return {}

    @property
    def schedule(self):
        """Return current schedule"""
        return self._schedule
    
    def sync(self):
        """Called periodically by Celery Beat to sync schedules"""
        logger.info("⏰ Periodic sync triggered")
        self.sync_from_db()
