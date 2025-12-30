from django.contrib.auth import get_user_model
from django.db.models.signals import *
from django.dispatch import receiver
from users.tasks import *

User = get_user_model()

# TODO сделать логирование входа/выхода

@receiver(pre_save, sender=User)
def user_changes(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_user = sender.objects.get(pk=instance.pk)
            changes = {}

            if old_user.username != instance.username:
                changes['username'] = {
                    'old': old_user.username,
                    'new': instance.username
                }

            if old_user.email != instance.email:
                changes['email'] = {
                    'old': old_user.email,
                    'new': instance.email
                }

            if instance.password != old_user.password:
                changes['password'] = True

            if changes:
                user_changes_logs_task.delay(
                    user_id=instance.pk,
                    changes=changes
                )

        except User.DoesNotExist:
            pass


@receiver(post_save, sender=DataFile)
def files_changes(sender, instance, **kwargs):
    if instance.pk:
        try:
            new_file = sender.objects.get(pk=instance.pk)
            changes = {}

            if new_file:
                changes['action'] = 'Create'
                changes['file'] = f'File: {new_file.file_name} was added'

            if changes:
                user_files_logs_task.delay(
                    user_id=instance.user_id,
                    changes=changes
                )

        except Exception as e:
            print(e)

@receiver(pre_delete, sender=DataFile)
def file_deletes(sender, instance, **kwargs):
    if instance.pk:
        try:
            deleted_file = sender.objects.get(pk=instance.pk)
            changes = {}
            if deleted_file:
                changes['action'] = 'Delete'
                changes['file'] = f'File: {deleted_file.file_name} was removed'

            if changes:
                user_files_logs_task.delay(
                    user_id=instance.user_id,
                    changes=changes
                )

        except Exception as e:
            print(e)
