from django.contrib import admin
from users.models import *

@admin.register(UserInOutInfo)
class UserInOutInfoAdmin(admin.ModelAdmin):
	list_display = ('id', 'updated_at', 'date', 'user', 'operation_type', 'amount', 'tag')
	search_fields = ('id', 'date', 'user__username', 'operation_type', 'amount', 'tag__tag')
	preserve_filters = True
	search_help_text = 'write: id, date, username, operation_type, amount, tag'
	list_select_related = ('user', 'tag')
	list_filter = ('user', 'tag__tag', 'operation_type', 'date')
	list_editable = ('date', 'tag', 'operation_type', 'amount')


@admin.register(OperationTags)
class OperationTagsAdmin(admin.ModelAdmin):
	list_display = ('id', 'tag')
	readonly_fields = ('slug',)
	search_fields = ('tag', 'id')


