from django.db.models.aggregates import *
from django.shortcuts import render
from django.shortcuts import redirect
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.serializers import *


def tpshka(request):
	if request.method == 'GET':
		return redirect('swagger-ui')


class OperationViewSet(viewsets.ModelViewSet):
	serializer_class = UserDataTagsSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		lookup_value = self.kwargs.get('pk')
		if not lookup_value:
			return UserInOutInfo.objects.all().select_related('user')
		else:
			return UserInOutInfo.objects.get(id=lookup_value)


class GraphViewSet(viewsets.ViewSet):  # Используем ViewSet вместо ModelViewSet
	permission_classes = [IsAuthenticated]

	def list(self, request):
		user = request.user
		month = request.GET.get('month')
		year = request.GET.get('year')

		monthly_data = UserInOutInfo.objects.filter(
			user=user,
			month=month,
			year=year
		).values('date__month', 'date__year').annotate(
			total_amount=Sum('amount'),
			count_operations=Count('id')
		).order_by('date__year', 'date__month')

		response_data = {
			'monthly_data': list(monthly_data.values('total_amount', 'count_operations')),
			'charts': {
				'income_vs_expense': self.get_income_expense_data(user),
			}
		}

		return Response(response_data)

	def get_income_expense_data(self, user):
		return UserInOutInfo.objects.filter(
			user=user
		).values('operation_type').annotate(
			total=Sum('amount')
		)
