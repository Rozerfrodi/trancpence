from datetime import datetime
from pprint import pprint
from django.contrib.admin.templatetags.admin_list import pagination
from rest_framework.pagination import PageNumberPagination
from django.db.models import F, Case, When, DecimalField, Lookup
from django.db.models.aggregates import *
from django.shortcuts import redirect
from rest_framework.viewsets import ViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.serializers import *
from users.models import OperationTags


def tpshka(request):
    if request.method == 'GET':
        return redirect('redoc')


class OperationViewSet(ReadOnlyModelViewSet):
    serializer_class = UserDataTagsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        lookup_value = self.kwargs.get('pk')
        if not lookup_value or lookup_value == '':
            return UserInOutInfo.objects.all().select_related('user', 'tag')
        else:
            return UserInOutInfo.objects.filter(id=lookup_value)


def base_queryset(*args, **kwargs):

    user, date_start, date_end, tags = args[0][:4]

    filters = {
        'user': user,
        'date__range': (date_start, date_end),
        'tag__tag__in': tags,
    }

    if kwargs.get('mode') == 'graph':
        return UserInOutInfo.objects.filter(**filters).select_related('user', 'tag')

    q, op_type, max_sum, min_sum, desc = args[0][4:]

    if q:
        filters['title__search'] = q

    if op_type:
        filters['operation_type__in'] = op_type

    if max_sum and min_sum:
        filters['amount__range'] = (int(min_sum), int(max_sum))

    elif min_sum:
        filters['amount__gte'] = min_sum

    elif max_sum:
        filters['amount__lte'] = max_sum


    if desc == 'ascending':
        return UserInOutInfo.objects.filter(**filters).order_by('amount').select_related('user', 'tag')
    elif desc == 'descending':
        return UserInOutInfo.objects.filter(**filters).order_by('-amount').select_related('user', 'tag')
    else:
        return UserInOutInfo.objects.filter(**filters).order_by('date').select_related('user', 'tag')

def param(self, request, *args, **kwargs):
    serializer = UserDataSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = request.user
    date_start = serializer.validated_data.get('date_start')
    date_end = serializer.validated_data.get('date_end')
    tags = serializer.validated_data.get('tags') if len(serializer.validated_data.get('tags')) > 0 \
        else list(OperationTags.objects.values_list('tag', flat=True))

    if isinstance(self, GraphViewSet):
        fields = (user, date_start, date_end, tags)
        output_serializer = GraphResponseSerializer(
            {"fields": fields, "view": self}
        )
    else:
        q = serializer.validated_data.get('q')
        op_type = serializer.validated_data.get('op_type')
        max_sum = serializer.validated_data.get('max_sum')
        min_sum = serializer.validated_data.get('min_sum')
        desc = serializer.validated_data.get('desc')
        fields = (user, date_start, date_end, tags, q, op_type, max_sum, min_sum, desc)
        output_serializer = GraphDetailsSerializer(
        {"fields": fields, "view": self}
    )

    return Response(output_serializer.data)


class GraphViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def params(self, request, *args, **kwargs):
        return param(self, request, *args, **kwargs)

    def get_period_total(self, *args):
        return base_queryset(*args, mode='graph').values('operation_type').annotate(
            total_amount=Sum('amount'),
            count_operations=Count('id')
        ).values('operation_type', 'total_amount', 'count_operations')

    def get_income_vs_expense(self, *args):
        result = base_queryset(*args, mode='graph').aggregate(
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

    def get_date_detail(self, *args):
        return base_queryset(*args, mode='graph').values('date').annotate(
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

    def get_tags_detail(self, *args):
        return base_queryset(*args, mode='graph').values(tags=F('tag__tag')).annotate(
            total_amount=Sum('amount')
        ).order_by('tag__tag')


class DetailViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    page_size = 10

    def params(self, request, *args, **kwargs):
        return param(self, request, *args, **kwargs)

    def get_details(self, *args):
        data = base_queryset(*args, mode='graph_ops').values(
            'id',
            'operation_type',
            'tag__svg',
            'date',
            'title',
            tags=F('tag__tag'),
        ).annotate(
            total=Sum('amount'),
        )
        paginator = self.pagination_class()
        paginator.page_size = self.page_size
        page = paginator.paginate_queryset(data, self.request, view=self)
        result = []
        for item in page:
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

        return paginator.get_paginated_response(result).data


class GetTagsAPIView(ViewSet):
    def list(self, request):
        tags = OperationTags.objects.values_list('tag', flat=True)
        return Response({'tags': list(tags)})
