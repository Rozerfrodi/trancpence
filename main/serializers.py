from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.conf import settings
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from users.models import UserInOutInfo
from .models import *
from taggit.serializers import (TagListSerializerField,
                                TaggitSerializer)

class UserDataTagsSerializer(TaggitSerializer ,serializers.ModelSerializer):
	tag = TagListSerializerField()
	class Meta:
		model = UserInOutInfo
		fields = ('id', 'title', 'date', 'created_at', 'operation_type', 'tag', 'amount')


