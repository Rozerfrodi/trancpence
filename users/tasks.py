from celery import shared_task
from django.db import connection


@shared_task(
             bind=True,
             acks_late=True
)
def clean_logs(self):
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE trancpencebd.drf_api_logs;")
        print('Logs cleaned')
