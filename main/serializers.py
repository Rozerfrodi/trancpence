from rest_framework import serializers
from users.models import UserInOutInfo


class UserDataTagsSerializer(serializers.ModelSerializer):
	tag = serializers.CharField(source='tag.tag')
	amount = serializers.FloatField()
	svg = serializers.CharField(source='tag.svg')
	created_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
	class Meta:
		model = UserInOutInfo
		fields = ('id', 'title', 'date', 'created_at', 'operation_type', 'tag', 'amount', 'svg')


class UserDataSerializer(serializers.Serializer):
	date_start = serializers.DateField(required=False)
	date_end = serializers.DateField(required=False)
	tags = serializers.ListField(allow_empty=True)