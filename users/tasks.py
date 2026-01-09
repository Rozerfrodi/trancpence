from datetime import datetime
from calendar import month
from decimal import Decimal
from pyexpat.errors import messages
from users.services.compare_mesage import get_stability_advice
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Case, When, DecimalField, F, CharField, Sum, StdDev, Q
from django.db.models.functions import Round, Coalesce
from calendar import monthrange
from users.models import *

date_now = (datetime.now().year, datetime.now().month)

@shared_task(
             bind=True,
             acks_late=True
)
def clean_logs(self):
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(id) FROM trancpencebd.drf_api_logs;")
        a = cursor.fetchone()[0]
        cursor.execute("TRUNCATE TABLE trancpencebd.drf_api_logs;")
    print(f'{a} Logs cleaned')

User = get_user_model()

@shared_task
def user_changes_logs_task(user_id, changes):
    try:
        user = User.objects.get(pk=user_id)

        for field, change_data in changes.items():
            if field == 'username':
                UserActionLog.objects.create(
                    user=user,
                    action_type='Change',
                    action_svg_id=1,
                    details=f"Username changed from {change_data['old']} to {change_data['new']}",
                )
            elif field == 'eyearmail':
                UserActionLog.objects.create(
                    user=user,
                    action_type='Change',
                    action_svg_id=1,
                    details=f"Email changed from {change_data['old']} to {change_data['new']}",
                )
            elif field == 'password':
                UserActionLog.objects.create(
                    user=user,
                    action_type='Change',
                    action_svg_id=1,
                    details="Password was changed",
                )

    except User.DoesNotExist:
        pass


@shared_task
def user_files_logs_task(user_id, changes):
    try:
        user = User.objects.get(pk=user_id)
        if changes['action'] == 'Create':
            UserActionLog.objects.create(
                user=user,
                action_type='Create',
                action_svg_id=3,
                details=changes['file'],
            )

        elif changes['action'] == 'Delete':
            UserActionLog.objects.create(
                user=user,
                action_type='Delete',
                action_svg_id=2,
                details=changes['file'],
            )

    except User.DoesNotExist:
        pass

@shared_task
def user_auth_logs_task(user_id, changes):
    try:
        user = User.objects.get(pk=user_id)
        UserActionLog.objects.create(
            user=user,
            action_type='Action',
            action_svg_id=4,
            details=changes['detail'],
        )

    except User.DoesNotExist:
        pass


@shared_task
def show_user_logs_task(user_id, request_type, period : dict = date_now, tags=None):
    logs = None
    try:
        if request_type == 'post':
            user = User.objects.get(pk=user_id)
            logs = UserActionLog.objects.filter(
                user=user,
                created_at__range=(period['from'], period['to']),
                action_type__in=tags if tags else ['Create', 'Delete', 'Action', 'Change'],
            )
        if request_type == 'get':
            user = User.objects.get(pk=user_id)
            logs = UserActionLog.objects.filter(
                user=user,
                created_at__year=date_now[0],
                created_at__month= date_now[1]
            )

        from .serializers import UserLogsSerializer
        serializer = UserLogsSerializer(logs, many=True)
        return serializer.data

    except User.DoesNotExist:
        return []
    except Exception as e:
        print(e)
        return []


def year_stats_func(user, periods):
    answer = {}
    for step, year in enumerate(periods):
        step = 'first' if step == 0 else 'second'
        answer[f'{step}_data_year'] = UserInOutInfo.objects.filter(
            user=user,
            date__year=year
        ).aggregate(
            total_incomes=Round(Coalesce(
                Sum('amount', filter=Q(operation_type='income')),
                DecimalField('0.00')
            ),
                2
            ),
            total_expenses=Round(Coalesce(
                Sum('amount', filter=Q(operation_type='expense')),
                DecimalField('0.00')
            ),
                2
            ),
            avg_stddev=StdDev(
                Case(When(operation_type='expense', then=F('amount')), default=None,
                     output_field=DecimalField()
                     )
            ),
        )
        answer[f'{step}_tag_top_year'] = UserInOutInfo.objects.filter(
            user=user,
            date__year=year
        ).values('date__year', 'tag__tag').annotate(
            top_tag=Sum(
                Case(When(operation_type='expense', then=F('amount')), default=0,
                     output_field=DecimalField()
                     )
            ),
        ).values('tag__tag', 'top_tag').order_by('-top_tag').first()
    return answer


def month_stats_func(user, periods):
    answer = {}
    for step, date in enumerate(periods):
        step = 'first' if step == 0 else 'second'
        answer[f'{step}_data_month'] = UserInOutInfo.objects.filter(
            user=user,
            date__year=date['year'],
            date__month=date['month'],
        ).aggregate(
            total_incomes=Round(Coalesce(
                Sum('amount', filter=Q(operation_type='income')),
                DecimalField('0.00')
            ),
                2
            ),
            total_expenses=Round(Coalesce(
                Sum('amount', filter=Q(operation_type='expense')),
                DecimalField('0.00')
            ),
                2
            ),
            avg_stddev=StdDev(
                Case(When(operation_type='expense', then=F('amount')), default=None,
                     output_field=DecimalField()
                     )
            ),
        )
        answer[f'{step}_tag_top_month'] = UserInOutInfo.objects.filter(
            user=user,
            date__year=date['year'],
            date__month=date['month'],
        ).values('date__year', 'tag__tag').annotate(
            top_tag=Sum(
                Case(When(operation_type='expense', then=F('amount')), default=0,
                     output_field=DecimalField()
                     )
            ),
        ).values('tag__tag', 'top_tag').order_by('-top_tag').first()
        answer[f'{step}_days_avg'] = UserInOutInfo.objects.filter(
            user=user,
            date__year=date['year'],
            date__month=date['month'],
        ).values('date__day').annotate(
            #TODO Доделать
        )
    return answer

def my_round(example):
    example = example.quantize(Decimal('0.01'))
    return example

@shared_task
def compare_year_logic_task(user_id, periods):
    first_year = periods['first_year']
    second_year = periods['second_year']
    data_year = None
    finally_answer = {}
    try:
        user = User.objects.get(pk=user_id)
        if user:
            data_year = year_stats_func(user, (first_year, second_year))

        for step in range(2):
            step = 'first' if step == 0 else 'second'
            year_exp = data_year.get(f'{step}_data_year').get('total_expenses', 0)
            year_inc = data_year.get(f'{step}_data_year').get('total_incomes', 0)
            avg_stddev = data_year.get(f'{step}_data_year').get('avg_stddev', 0)
            finally_answer[f'{step}_year_stats'] = \
                {
                    'total_incomes': year_inc,
                    'total_expenses': year_exp,
                    'top_tag': data_year.get(f'{step}_tag_top_year').get('tag__tag'),
                    'net_profit': my_round(year_inc - year_exp),
                    'inc_exp_ratio': my_round(year_exp / year_inc) if year_exp is not None else 0,
                }

            finally_answer[f'{step}_avg_year_stats'] = \
                {
                    'avg_monthly_incomes': my_round(year_inc / 12),
                    'avg_monthly_expenses': my_round(year_exp / 12),
                    'avg_monthly_saving': my_round((year_inc - year_exp) / 12),
                    'avg_stddev': my_round(avg_stddev) if avg_stddev is not None else 0,
                }

        f_year_exp = finally_answer.get('first_year_stats').get('total_expenses')
        s_year_exp = finally_answer.get('second_year_stats').get('total_expenses')
        f_year_inc = finally_answer.get('first_year_stats').get('total_incomes')
        s_year_inc = finally_answer.get('second_year_stats').get('total_incomes')
        f_avg_stddev = finally_answer.get('first_avg_year_stats').get('avg_stddev')
        s_avg_stddev = finally_answer.get('second_avg_year_stats').get('avg_stddev')
        stddev_comparison = ((s_avg_stddev - f_avg_stddev) / f_avg_stddev) * 100
        inc_comparison = f_year_inc - s_year_exp
        percent_inc_vs_inc = ((s_year_inc - f_year_inc) / f_year_inc) * 100
        exp_comparison = f_year_exp - s_year_exp
        percent_exp_vs_exp = ((s_year_exp - f_year_exp) / f_year_exp) * 100
        finally_answer['year_comparison'] = \
            {
                'inc_comparison': my_round(inc_comparison),
                'percent_inc_vs_inc': my_round(percent_inc_vs_inc),
                'exp_comparison': my_round(exp_comparison),
                'percent_exp_vs_exp': my_round(percent_exp_vs_exp),
                'stddev_comparison': get_stability_advice(my_round(stddev_comparison)),
            }

        return finally_answer

    except User.DoesNotExist:
        return []

@shared_task
def compare_month_logic_task(user_id, periods):
    first_month = periods['first_month']
    second_month = periods['second_month']
    f_day_count = monthrange(first_month['year'], first_month['month'])[1]
    s_day_count = monthrange(second_month['year'], second_month['month'])[1]

    finally_answer = {}

    data_month = None
    try:
        user = User.objects.get(pk=user_id)
        if user:
            data_month = month_stats_func(user, (first_month, second_month))

        for step in range(2):
            step = 'first' if step == 0 else 'second'

            month_exp = data_month.get(f'{step}_data_month').get('total_expenses', 0)
            month_inc = data_month.get(f'{step}_data_month').get('total_incomes', 0)
            avg_stddev = data_month.get(f'{step}_data_month').get('avg_stddev', 0)
            top_tag = data_month.get(f'{step}_tag_top_month').get('tag__tag', 'N/A')
            days = f_day_count if step == 'first' else s_day_count

            finally_answer[f'{step}_month_stats'] = \
                {
                    'total_incomes': month_inc,
                    'total_expenses': month_exp,
                    'top_tag': top_tag,
                    'net_profit': my_round(month_inc - month_exp),
                    'inc_exp_ratio': my_round(month_exp / month_inc) if month_exp is not None else 0,
                }

            finally_answer[f'{step}_avg_month_stats'] = \
                {
                    'avg_monthly_incomes': my_round(month_inc / days),
                    'avg_monthly_expenses': my_round(month_exp / days),
                    'avg_monthly_saving': my_round((month_inc - month_exp) / days),
                    'avg_stddev': my_round(avg_stddev) if avg_stddev is not None else 0,
                }

        f_month_exp = finally_answer.get('first_month_stats').get('total_expenses')
        s_month_exp = finally_answer.get('second_month_stats').get('total_expenses')
        f_month_inc = finally_answer.get('first_month_stats').get('total_incomes')
        s_month_inc = finally_answer.get('second_month_stats').get('total_incomes')
        f_avg_stddev = finally_answer.get('first_avg_month_stats').get('avg_stddev')
        s_avg_stddev = finally_answer.get('second_avg_month_stats').get('avg_stddev')

        stddev_comparison = ((s_avg_stddev - f_avg_stddev) / f_avg_stddev) * 100
        inc_comparison = f_month_inc - s_month_inc
        percent_inc_vs_inc = ((s_month_inc - f_month_inc) / f_month_inc) * 100
        exp_comparison = f_month_exp - s_month_exp
        percent_exp_vs_exp = ((s_month_exp - f_month_exp) / f_month_exp) * 100
        finally_answer['month_comparison'] = \
            {
                'inc_comparison': my_round(inc_comparison),
                'percent_inc_vs_inc': my_round(percent_inc_vs_inc),
                'exp_comparison': my_round(exp_comparison),
                'percent_exp_vs_exp': my_round(percent_exp_vs_exp),
                'stddev_comparison': get_stability_advice(my_round(stddev_comparison)),
            }

        return finally_answer

    except User.DoesNotExist:
        return []
