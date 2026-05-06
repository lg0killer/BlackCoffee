import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blackcoffee.settings')

app = Celery('blackcoffee')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

from celery.schedules import crontab

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'fetch-joke-of-the-day-midnight-utc': {
        'task': 'dadjokes.tasks.fetch_joke_of_the_day',
        'schedule': crontab(minute=0, hour=0),  # Midnight UTC
    },
    'process-notifications-every-minute': {
        'task': 'notifications.tasks.process_notifications',
        'schedule': crontab(minute='*'),  # Every minute
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
