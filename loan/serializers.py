from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from loan.models import *
from datetime import timedelta


class LoanSerializer(serializers.ModelSerializer):
    q = serializers.CharField(default='', required=False, write_only=True)
    date_start = serializers.DateField(required=False, write_only=True)
    date_end = serializers.DateField(required=False, write_only=True)
    loan_type = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False, write_only=True,
                                      default=['Mortgage', 'Loan', 'Other', 'Installment'])
    loan_name = serializers.CharField(required=False)

    class Meta:
        model = MainLoan
        exclude = ('user', 'down_payment', 'property_value', 'commission')

    def validate(self, attrs):
        if attrs.get('date_start') and attrs.get('date_end'):
            if attrs['date_start'] > attrs['date_end']:
                raise ValidationError('date_start must be before date_end')
            if attrs.get('min_sum', '') and attrs.get('max_sum', ''):
                if int(attrs.get('min_sum', '')) > int(attrs.get('max_sum', '')):
                    raise ValidationError('min_sum must be less than max_sum')
        return attrs

class LoanCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = MainLoan
        fields = '__all__'
        read_only_fields = ('created_at', 'edited_at')


class LoanDeleteSerializer(serializers.ModelSerializer):
    loan_list = serializers.ListField(child=serializers.IntegerField(), required=True, write_only=True)

    class Meta:
        model = MainLoan
        fields = ('id', 'loan_list')


class LoanUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = MainLoan
        exclude = ('user', 'id', 'created_at', 'edited_at')