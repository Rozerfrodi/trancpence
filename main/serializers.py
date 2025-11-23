from django.db.models import CharField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from users.models import UserInOutInfo


class UserDataTagsSerializer(serializers.ModelSerializer):
	tag = serializers.CharField(source='tag.tag')
	amount = serializers.SerializerMethodField()
	svg = serializers.CharField(source='tag.svg')
	created_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d')
	class Meta:
		model = UserInOutInfo
		fields = ('id', 'title', 'date', 'created_at', 'operation_type', 'tag', 'amount', 'svg')

	def get_amount(self, obj):
		if obj.operation_type == 'expense':
			return -abs(obj.amount)
		return obj.amount

class UserDataSerializer(serializers.Serializer):
	date_start = serializers.DateField(required=True)
	date_end = serializers.DateField(required=True)
	tags = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=True)

	def validate(self, attrs):
		if attrs['date_start'] > attrs['date_end']:
			raise ValidationError('date_start must be before date_end')
		return attrs