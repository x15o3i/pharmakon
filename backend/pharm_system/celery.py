import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharm_system.settings')

app = Celery('pharm_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Scheduled Tasks
app.conf.beat_schedule = {
    'check-expiring-drugs-daily': {
        'task': 'alerts.tasks.check_expiring_drugs',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'escalate-unacknowledged-alerts-daily': {
        'task': 'alerts.tasks.escalate_unacknowledged_alerts',
        'schedule': crontab(hour=6, minute=0),  # Daily at 6 AM
    },
}
