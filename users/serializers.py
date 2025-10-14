from datetime import datetime
import openpyxl
from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.conf import settings
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import *
from djoser.serializers import (
	UserSerializer as BaseUserSerializer,
	UserCreateSerializer as BaseUserCreateSerializer, UsernameSerializer)


User = get_user_model()

class CustomUserCreateSerializer(BaseUserCreateSerializer):
	file = serializers.FileField(required=True, write_only=True)

	class Meta(BaseUserCreateSerializer.Meta):
		model = User
		fields = ['email', 'username', 'password', 'file']

	def validate(self, attrs):
		self._file = attrs.pop('file', None)
		return super().validate(attrs)

	def create(self, validated_data):
		user = super().create(validated_data)
		if self._file:
			self.import_transaction(user, self._file)
		return user

	def import_transaction(self, user, file):
		try:
			wb = openpyxl.load_workbook(file)
			sheet = wb.active

			transactions_to_create = []

			for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, values_only=True):
				date, title, suma = row

				if isinstance(date, str):
					transaction_date = datetime.strptime(date, '%Y-%m-%d').date()
				else:
					transaction_date = date.date()

				transaction_obj = UserInOutInfo(
					user=user,
					date=transaction_date,
					title=title,
					operation_type='income' if suma > 0 else 'expense',
					amount=abs(suma) if suma < 0 else suma,
				)
				transactions_to_create.append(transaction_obj)

			if transactions_to_create:
				with transaction.atomic():
					UserInOutInfo.objects.bulk_create(transactions_to_create)

		except Exception as e:
			print(f'error transaction: {e}')


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