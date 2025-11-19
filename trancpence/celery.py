
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trancpence.settings')

from celery import Celery
from trancpence.settings import CELERY

app = Celery('trancpence')
app.config_from_object(CELERY)
app.autodiscover_tasks()
