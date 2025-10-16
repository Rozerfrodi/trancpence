from datetime import datetime
from pprint import pprint
from django.db.models import Func
from rest_framework_extensions.cache.mixins import CacheResponseMixin
from django.db.models import F, Case, When, DecimalField
from django.db.models.aggregates import *
from django.shortcuts import redirect
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.serializers import *
from users.models import OperationTags


class MonthYear(Func):
	function = 'DATE_FORMAT'
	template = "%(function)s(%(expressions)s, '%%%%M %%%%Y')"

def tpshka(request):
	if request.method == 'GET':
		return redirect('swagger-ui')


class OperationViewSet(viewsets.ModelViewSet):
	serializer_class = UserDataTagsSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		lookup_value = self.kwargs.get('pk')
		if not lookup_value or lookup_value=='':
			return UserInOutInfo.objects.all().select_related('user', 'tag')
		else:
			return UserInOutInfo.objects.filter(id=lookup_value)


class GraphViewSet(CacheResponseMixin, viewsets.ViewSet):
	permission_classes = [IsAuthenticated]

	__date_now = str(datetime.now().date())
	__tags = OperationTags.objects.values('tag')
	__user = None
	__date_start = "2025-10-01"
	__date_end = "2025-10-31"

	def params(self, request, *args, **kwargs):
		serializer = UserDataSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		self.__user = request.user
		self.__date_start = serializer.validated_data['date_start'] or self.__date_start
		self.__date_end = serializer.validated_data['date_end'] or self.__date_end
		self.__tags = serializer.validated_data['tags'] or self.__tags

		response_data = {
			'total': list(self.monthly_data().values('date__month', 'operation_type', 'total_amount', 'count_operations')),
			'income vs expense': self.get_income_vs_expense(),
			'details': self.get_details(),
			'date_detail': self.date_detail(),
			'tags_detail': self.tags_detail(),
		}
		return Response(response_data)

	def monthly_data(self):
		return UserInOutInfo.objects.filter(
			user=self.__user,
			date__range=(self.__date_start, self.__date_end),
			tag__tag__in=self.__tags,
		).values('date__month', 'date__year').annotate(
			total_amount=Sum('amount'),
			count_operations=Count('id')
		).order_by('date__year', 'date__month')

	def get_income_vs_expense(self):
		result = UserInOutInfo.objects.filter(
			user=self.__user,
			tag__tag__in=self.__tags,
			date__range=(self.__date_start, self.__date_end)
		).select_related('user', 'tag').aggregate(
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


	def get_details(self):
		data = UserInOutInfo.objects.filter(
			user=self.__user,
			tag__tag__in=self.__tags,
			date__range=(self.__date_start, self.__date_end)

		).select_related('user', 'tag').values('operation_type', 'tag__svg', 'date', 'title',
		                                       tags=F('tag__tag')).annotate(
			total=Sum('amount'),
		).order_by('operation_type', 'total')
		result = []
		for item in data:
			op_type = item['operation_type']
			result.append({
				'tags': item['tags'],
				'operation_type': op_type,
				'title': item['title'],
				'date': item['date'],
				'total': item['total'] if op_type == 'income' else -item['total'],
				'svg': item['tag__svg'],
			})
		return result


	def date_detail(self):
		return UserInOutInfo.objects.filter(
			user=self.__user,
			tag__tag__in=self.__tags,
			date__range=(self.__date_start, self.__date_end)
		).select_related('user', 'tag').values('date').annotate(
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

	def tags_detail(self):
		return UserInOutInfo.objects.filter(
			user=self.__user,
			date__range=(self.__date_start, self.__date_end),
			tag__tag__in=self.__tags
		).select_related('user', 'tag').values(tags=F('tag__tag')).annotate(
			total_amount=Sum('amount')
		).order_by('tag__tag')

class GetTagsAPIView(viewsets.ViewSet):
	def list(self, request):
		response_data = {'tags': self.get_tags()}
		return Response(response_data)

	def get_tags(self):
		e = OperationTags.objects.values('tag')
		itog = [a for a in e]
		a = []
		for i in itog:
			a.append(i['tag'])
		return a