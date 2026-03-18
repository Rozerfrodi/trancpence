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
    q = serializers.CharField(required=False, allow_blank=True)
    op_type = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    max_sum = serializers.CharField(required=False, allow_blank=True, default='')
    min_sum = serializers.CharField(required=False, allow_blank=True, default='')
    desc = serializers.ChoiceField(choices=('ascending', 'descending', 'date'), required=False, default='date')

    def validate(self, attrs):
        if attrs['date_start'] > attrs['date_end']:
            raise ValidationError('date_start must be before date_end')
        if attrs.get('min_sum', '') and attrs.get('max_sum', ''):
            if int(attrs.get('min_sum', '')) > int(attrs.get('max_sum', '')):
                raise ValidationError('min_sum must be less than max_sum')
        return attrs


class GraphResponseSerializer(serializers.Serializer):
    total = serializers.SerializerMethodField()
    income_vs_expense = serializers.SerializerMethodField()
    date_detail = serializers.SerializerMethodField()
    tags_detail = serializers.SerializerMethodField()

    def get_total(self, obj):
        user, date_start, date_end, tags = obj["fields"]
        return obj["view"].get_period_total((user, date_start, date_end, tags))

    def get_income_vs_expense(self, obj):
        user, date_start, date_end, tags = obj["fields"]
        return obj["view"].get_income_vs_expense((user, date_start, date_end, tags))

    def get_date_detail(self, obj):
        user, date_start, date_end, tags = obj["fields"]
        return obj["view"].get_date_detail((user, date_start, date_end, tags))

    def get_tags_detail(self, obj):
        user, date_start, date_end, tags = obj["fields"]
        return obj["view"].get_tags_detail((user, date_start, date_end, tags))

    def get_details(self, obj):
        user, date_start, date_end, tags = obj["fields"]
        return obj["view"].get_details((user, date_start, date_end, tags))


class GraphDetailsSerializer(serializers.Serializer):
    details = serializers.SerializerMethodField()

    def get_details(self, obj):
        user, date_start, date_end, tags, q, op_type, max_sum, min_sum, desc = obj["fields"]
        return obj["view"].get_details((user, date_start, date_end, tags, q, op_type, max_sum, min_sum, desc))
