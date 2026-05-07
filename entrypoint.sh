#!/bin/bash
set -e

echo "Running database migrations..."
python manage.py migrate

# Initialize schedules if they don't exist
python manage.py shell -c "from django_celery_beat.models import PeriodicTask, IntervalSchedule; schedule_15, _ = IntervalSchedule.objects.get_or_create(every=15, period=IntervalSchedule.MINUTES); PeriodicTask.objects.get_or_create(name='Catchup Scrapers (Every 15 mins)', defaults={'interval': schedule_15, 'task': 'news.tasks.catchup_scrapers'})"

exec "$@"
