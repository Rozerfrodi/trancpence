from django.db.models import CharField
from rest_framework import serializers
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
	date_start = serializers.DateField(required=False)
	date_end = serializers.DateField(required=False)
	tags = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)