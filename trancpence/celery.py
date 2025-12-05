
import os

from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trancpence.settings')

from celery import Celery

app = Celery('trancpence')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'api-clear':{
        'task': 'users.tasks.clean_logs',
        'schedule': 3600.0,
    },
}