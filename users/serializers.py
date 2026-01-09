from django.contrib.auth import get_user_model
from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
import re
from main.serializers import UserDataSerializer
from .models import *
from .services.services import import_transaction
from djoser.serializers import UsernameSerializer, UserCreateSerializer

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    file = serializers.FileField(required=True, write_only=True)
    email = serializers.EmailField(required=True, write_only=True)
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
    file = serializers.ListField(
        child=serializers.FileField(),
        write_only=True
    )
    class Meta:
        model = DataFile
        read_only_fields = ('file_name', 'uploaded_at')
        fields = ('id', 'file', 'file_name', 'uploaded_at')

    def validate(self, attrs):
        file = attrs.get('file')
        for f in file:
            if not f.name.endswith('.xlsx'):
                raise serializers.ValidationError('File must be .xlsx file')
            if f.size > 5 * 1024 * 1024:
                raise serializers.ValidationError('File too big, > 5 mb')
        return attrs

class UserLogsSerializer(serializers.ModelSerializer):
    action_svg = serializers.CharField(source='action_svg.svg', read_only=True)
    action_color = serializers.CharField(source='action_svg.action_color', read_only=True)

    class Meta:
        model = UserActionLog
        fields = '__all__'

    def validate(self, attrs):
        if attrs['date_start'] > attrs['date_end']:
            raise ValidationError('date_start must be before date_end')
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

    def raise_error(self, errors):
        raise ValidationError(errors)


class CompareSerializer(serializers.Serializer):
    first_year = serializers.CharField(write_only=True, required=False)
    second_year = serializers.CharField(write_only=True, required=False)

    first_month = serializers.CharField(write_only=True, required=False)
    second_month = serializers.CharField(write_only=True, required=False)

    def validate(self, value):
        pattern_year = r'^\d{4}$'
        pattern_month = r'^\d{4}-\d{1,2}$'
        pattern_type = None
        for k, v in value.items():
            if k.endswith('year'):
                if not re.match(pattern_year, v):
                    raise serializers.ValidationError('year must be in format YYYY')
                pattern_type = 'yearly'
            elif k.endswith('month'):
                if not re.match(pattern_month, v):
                    raise serializers.ValidationError('date must be in format YYYY-MM')
                pattern_type = 'monthly'
            else:
                raise serializers.ValidationError('incorrect date format')

        if pattern_type == 'yearly':
            value['first_year'] = int(value['first_year'])
            value['second_year'] = int(value['second_year'])
            value['comp_type'] = pattern_type
            if value['first_year'] == value['second_year']:
                raise serializers.ValidationError('period must be different')
        elif pattern_type == 'monthly':
            value['first_month'] = {['year', 'month'][i]: list(map(int,(value['first_month'].split('-'))))[i] for i in range(2)}
            value['second_month'] = {['year', 'month'][i]: list(map(int,(value['second_month'].split('-'))))[i] for i in range(2)}
            value['comp_type'] = pattern_type
            if value['first_month']['month'] == value['second_month']['month']:
                raise serializers.ValidationError('year must be different')

        return value
