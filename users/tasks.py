from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import connection
from users.models import *


@shared_task(
             bind=True,
             acks_late=True
)
def clean_logs(self):
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE trancpencebd.drf_api_logs;")
        print('Logs cleaned')

User = get_user_model()

@shared_task
def user_changes_logs_task(user_id, changes):
    try:
        user = User.objects.get(pk=user_id)

        for field, change_data in changes.items():
            if field == 'username':
                UserActionLog.objects.create(
                    user=user,
                    action_type='Change',
                    action_svg_id=1,
                    details=f"Username changed from {change_data['old']} to {change_data['new']}",
                )
            elif field == 'email':
                UserActionLog.objects.create(
                    user=user,
                    action_type='Change',
                    action_svg_id=1,
                    details=f"Email changed from {change_data['old']} to {change_data['new']}",
                )
            elif field == 'password':
                UserActionLog.objects.create(
                    user=user,
                    action_type='Change',
                    action_svg_id=1,
                    details="Password was changed",
                )

    except User.DoesNotExist:
        pass


@shared_task
def user_files_logs_task(user_id, changes):
    try:
        user = User.objects.get(pk=user_id)
        if changes['action'] == 'Create':
            UserActionLog.objects.create(
                user=user,
                action_type='Create',
                action_svg_id=3,
                details=changes['file'],
            )

        elif changes['action'] == 'Delete':
            UserActionLog.objects.create(
                user=user,
                action_type='Delete',
                action_svg_id=2,
                details=changes['file'],
            )

    except User.DoesNotExist:
        pass

