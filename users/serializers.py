from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import *
from .services.services import import_transaction
from djoser.serializers import UsernameSerializer, UserCreateSerializer

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
	file = serializers.FileField(required=True, write_only=True)

	class Meta(UserCreateSerializer.Meta):
		model = User
		fields = ['email', 'username', 'password', 'file']

	def validate(self, attrs):
		self._file = attrs.pop('file', None)
		return super().validate(attrs)

	def create(self, validated_data):
		user = super().create(validated_data)
		if self._file:
			import_result = import_transaction(user, self._file, True)
			user.import_result = import_result
		return user

	def to_representation(self, instance):
		data = super().to_representation(instance)
		if hasattr(instance, 'import_result'):
			data['import_result'] = instance.import_result
		return data


class FileSerializer(serializers.ModelSerializer):

	class Meta:
		model = DataFile
		read_only_fields = ('file_name', 'uploaded_at')
		fields = ('id', 'file', 'file_name', 'uploaded_at')

	def validate(self, attrs):
		file = attrs.get('file')
		if file.size > 5 * 1024 * 1024:
			raise serializers.ValidationError('File too big, > 5 mb')
		return attrs


class CustomSetUsernameSerializer(UsernameSerializer):
	class Meta:
		model = User
		fields = ('username',)

	def validate(self, value):
		if User.objects.filter(username=value).exists():
			raise serializers.ValidationError("This username already exists.")
		return value


class CustomSetEmailSerializer(serializers.ModelSerializer):
	email = serializers.EmailField(required=True)

	class Meta:
		model = User
		fields = ('email',)

	def validate_email(self, value):
		if User.objects.filter(email=value).exclude(id=self.context['request'].user.id).exists():
			raise serializers.ValidationError("Email already exists.")
		return value

	def validate(self, attrs):
		attrs = super().validate(attrs)
		return attrs

