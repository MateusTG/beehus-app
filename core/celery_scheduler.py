import logging
from celery.beat import Scheduler, ScheduleEntry
from celery import current_app
from core.models.mongo_models import Job
from core.db import init_db
import asyncio
from celery.schedules import crontab

logger = logging.getLogger(__name__)

class MongoScheduleEntry(ScheduleEntry):
    def __init__(self, name, task, last_run_at=None, total_run_count=None,
                 schedule=None, args=(), kwargs=None, options=None,
                 relative=False, app=None):
        super().__init__(name, task, last_run_at, total_run_count,
                         schedule, args, kwargs, options, relative, app)

class MongoScheduler(Scheduler):
    Entry = MongoScheduleEntry

    def __init__(self, *args, **kwargs):
        self._schedule = {}
        super().__init__(*args, **kwargs)
        self.max_interval = 60  # Sync with DB every 60 seconds

    def setup_schedule(self):
        self.install_default_entries(self._schedule)
        self.sync_data()

    def sync_data(self):
        """Sync schedule from MongoDB"""
        logger.info("🔄 Syncing Celery Beat schedule from MongoDB...")
        try:
            # We need to run async DB code in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            new_schedule = loop.run_until_complete(self._get_jobs_from_db())
            loop.close()

            # Update schedule
            self.merge_inplace(new_schedule)
            logger.info(f"✅ Synced {len(new_schedule)} periodic jobs")
        except Exception as e:
            logger.error(f"❌ Failed to sync schedule: {e}")

    async def _get_jobs_from_db(self):
        try:
            await init_db()
            logger.info("🔍 Querying MongoDB for scheduled jobs...")
            
            # Query all jobs first to see what we have
            all_jobs = await Job.find_all().to_list()
            logger.info(f"📊 Total jobs in database: {len(all_jobs)}")
            
            # Query for scheduled jobs
            jobs = await Job.find(
                Job.status == "active",
                Job.schedule != None,
                Job.schedule != ""
            ).to_list()
            
            logger.info(f"📅 Jobs with schedules: {len(jobs)}")
            for job in all_jobs:
                logger.info(f"  - Job {job.id}: status={job.status}, schedule={job.schedule}")

            schedule = {}
            for job in jobs:
                try:
                    # Assuming simple cron: "minute hour day month day_of_week"
                    # TODO: Add validation or robust parsing
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
        if not self._schedule:
            self.sync_data()
        return self._schedule
    
    def needs_update(self):
        """Check if we need to sync from DB"""
        # For now, we rely on the loop period (max_interval) calling sync
        # But explicitly returning True forces a sync check if implemented in loop
        return True

    def tick(self, event_t=None, sleeping=False):
        # Override tick to sync periodically
        # In default Scheduler, tick calls sync(). 
        # But we want to enforce DB sync.
        
        # NOTE: simplistic approach. proper way is to rely on max_interval
        # and checking for modifications. 
        # Here we just blindly reload on every sync interval (controlled by max_interval)
        if self._heap is None:
             self.sync_data()
        
        return super().tick(event_t, sleeping)

    def sync(self):
        self.sync_data()
        super().sync()
