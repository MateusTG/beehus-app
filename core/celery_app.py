from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_config.settings')

app = Celery('beehus')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in core module
app.autodiscover_tasks(['core'])

# Celery Beat configuration
# Static System Tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-stale-runs': {
        'task': 'core.tasks.cleanup_stale_runs',
        'schedule': 300.0,  # Run every 5 minutes
        'options': {'queue': 'celery'} # Run on default queue
    },
    'sync-mongo-schedule': {
         # Force sync every minute (backup for custom scheduler internal loop)
         # actually custom scheduler does this internally, but explicit task is fine too if we needed it.
         # For now, just cleanup is enough.
         'task': 'core.tasks.cleanup_old_runs_task',
         'schedule': crontab(hour=0, minute=0), # Daily midnight
         'args': (30,) # Keep 30 days
    }
}

@app.task(bind=True)
def debug_task(self):
    """Simple debug task for testing Celery"""
    print(f'Request: {self.request!r}')
    return 'Debug task completed'


