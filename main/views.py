from datetime import datetime
from pprint import pprint
from rest_framework_extensions.cache.mixins import CacheResponseMixin
from django.db.models import F, Case, When, DecimalField
from django.db.models.aggregates import *
from django.shortcuts import redirect
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.serializers import *
from users.models import OperationTags
from django.core.cache import cache

# class MonthYear(Func):
# 	function = 'DATE_FORMAT'
# 	template = "%(function)s(%(expressions)s, '%%%%M %%%%Y')"

def tpshka(request):
	if request.method == 'GET':
		return redirect('swagger-ui')


class OperationViewSet(viewsets.ModelViewSet):
	serializer_class = UserDataTagsSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		lookup_value = self.kwargs.get('pk')
		if not lookup_value or lookup_value == '':
			return UserInOutInfo.objects.all().select_related('user', 'tag')
		else:
			return UserInOutInfo.objects.filter(id=lookup_value)


class GraphViewSet(CacheResponseMixin, viewsets.ViewSet):
	permission_classes = [IsAuthenticated]

	def params(self, request, *args, **kwargs):
		serializer = UserDataSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = request.user
		date_start = serializer.validated_data.get('date_start')
		date_end = serializer.validated_data.get('date_end')
		tags = serializer.validated_data.get('tags') if len(
			serializer.validated_data.get('tags')) > 0 else list(OperationTags.objects.values_list('tag', flat=True))
		fields = (user, date_start, date_end, tags)

		response_data = {
			'total': self.period_total(fields),
			'income_vs_expense': self.get_income_vs_expense(fields),
			'date_detail': self.date_detail(fields),
			'tags_detail': self.tags_detail(fields),
			'details': self.get_details(fields),
		}

		return Response(response_data)

	def base_queryset(self, *args):
		return UserInOutInfo.objects.filter(
			user=args[0][0],
			date__range=(args[0][1], args[0][2]),
			tag__tag__in=args[0][3],
		).select_related('user', 'tag')

	def period_total(self, *args):
		return self.base_queryset(*args).values('operation_type').annotate(
			total_amount=Sum('amount'),
			count_operations=Count('id')
		).values('operation_type', 'total_amount', 'count_operations')

	def get_income_vs_expense(self, *args):
		result = self.base_queryset(*args).aggregate(
			total=Sum(
				Case(
					When(operation_type='income', then='amount'),
					When(operation_type='expense', then=-F('amount')),
					default=0,
					output_field=DecimalField()
				)
			)
		)
		return result['total'] or 0

	def get_details(self, *args):
		data = self.base_queryset(*args).values('id', 'operation_type', 'tag__svg', 'date', 'title',
		    tags=F('tag__tag')).annotate(
			total=Sum('amount'),
		).order_by('date')
		result = []
		for item in data:
			op_type = item['operation_type']
			result.append({
				'id': item['id'],
				'tags': item['tags'],
				'operation_type': op_type,
				'title': item['title'],
				'date': item['date'],
				'total': item['total'] if op_type == 'income' else -item['total'],
				'svg': item['tag__svg'],
			})
		return result

	def date_detail(self, *args):
		return self.base_queryset(*args).values('date').annotate(
			incomes=Sum(
				Case(
					When(operation_type='income', then=F('amount')),
					default=0,
					output_field=DecimalField()
				)
			),
			expenses=Sum(
				Case(
					When(operation_type='expense', then=-F('amount')),
					default=0,
					output_field=DecimalField()
				)
			)
		).order_by('date')

	def tags_detail(self, *args):
		return self.base_queryset(*args).values(tags=F('tag__tag')).annotate(
			total_amount=Sum('amount')
		).order_by('tag__tag')


class GetTagsAPIView(viewsets.ViewSet):
	def list(self, request):
		tags = OperationTags.objects.values_list('tag', flat=True)
		return Response({'tags': list(tags)})
