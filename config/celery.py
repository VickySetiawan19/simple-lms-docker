import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Load config from Django settings, using CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# =============================================
# CELERY BEAT SCHEDULE (Scheduled Tasks)
# =============================================
app.conf.beat_schedule = {
    # update_enrollment_statistics berjalan setiap jam sekali
    'update-enrollment-statistics-every-hour': {
        'task': 'courses.tasks.update_enrollment_statistics',
        'schedule': crontab(minute=0),  # setiap jam tepat
    },
    # cleanup_expired_data berjalan setiap hari jam 2 pagi
    'cleanup-expired-data-daily': {
        'task': 'courses.tasks.cleanup_expired_data',
        'schedule': crontab(hour=2, minute=0),  # jam 2:00
    },
    # sync_learning_analytics berjalan setiap 6 jam
    'sync-learning-analytics-every-6h': {
        'task': 'courses.tasks.sync_learning_analytics',
        'schedule': crontab(minute=0, hour='*/6'),  # 00:00, 06:00, 12:00, 18:00
    },
}

app.conf.timezone = 'Asia/Jakarta'