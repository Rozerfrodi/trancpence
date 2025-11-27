
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trancpence.settings')

from celery import Celery

app = Celery('trancpence')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
