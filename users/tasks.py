from celery import shared_task
from django.db import connection


@shared_task(bind=True)
def clean_logs(self):
    try:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE trancpencebd.drf_api_logs;")
        self.logger.info('API logs cleaned successfully')
    except Exception as e:
        self.logger.error(f'Error cleaning API logs: {e}')
        raise

