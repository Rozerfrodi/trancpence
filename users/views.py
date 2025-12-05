from datetime import date
from django.db.models import Count, Case, Sum, F, When, DecimalField
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from djoser.views import UserViewSet
from djoser import utils
from django.http import HttpResponse, HttpResponseNotFound, FileResponse, HttpResponseBadRequest
from django.contrib.auth.tokens import default_token_generator
from rest_framework.response import Response
from users.serializers import *
from rest_framework.viewsets import ViewSet
import os
import trancpence.settings as settings

User = get_user_model()


def get_example_file(request):
    file_path = os.path.join(settings.BASE_DIR, 'files', 'example.xlsx')
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='example.xlsx')


class CustomUserViewSet(UserViewSet, ViewSet):

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if instance == request.user:
            utils.logout_user(self.request)
        files_list = [i['id']for i in DataFile.objects.filter(user=instance).values('id')]
        if DataFile.objects.filter(id__in=files_list).exists():
            count = 0
            for i in files_list:
                DataFile.objects.get(id=i, user=request.user).delete()
                count += 1
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
        serializer_class=CustomSetEmailSerializer
    )
    def set_email(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.email = serializer.validated_data['email']
        user.save()

        return Response(
            {'detail': 'Email successful changed', 'email': user.email}
        )

    @action(
        detail=False,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
        serializer_class=CustomSetUsernameSerializer
    )
    def set_username(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.username = serializer.validated_data['username']
        user.save()

        return Response(
            {'detail': 'Username successful changed', 'username': user.username}
        )

    @action(methods=['post'], detail=False)
    def activate_user_redirect(self, request, uid, token):
        try:
            uid_decoded = utils.decode_uid(uid)
            user = User.objects.get(pk=uid_decoded)
            token_obj = default_token_generator.check_token(user, token)
            if token_obj:
                if not user.is_active:
                    user.is_active = True
                    user.save()
                    return HttpResponse({
                        "<p>Account activated successfully</p>"
                        "<a href='http://172.30.181.190:5173/login'>Visit signin page</a>"
                        "<hr></hr>"
                    })
                else:
                    return HttpResponse({
                        "<p>Account was already activated</p><a href='http://172.30.181.190:5173/login'>Visit signin page</a>"
                        "<hr></hr>"
                        "<p>or contact with administration 'rostislavovvseslav@gmail.com'</p>"
                    })
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return HttpResponseNotFound()

    @action(methods=['get'], detail=False)
    def stats(self, request):
        user = request.user
        bi = self.biggest_spending_month(user)
        in_out = self.income_expenses(user)
        if not isinstance(bi, str):
            return Response(
                {
                    "added_files": self.added_files(user),
                    "incomes": in_out.get('total_incomes'),
                    "expenses": in_out.get('total_expenses'),
                    "most_valuable_category": self.most_valuable_category(user),
                    "biggest_spending_month": {
                        "year": bi.get('date__year'),
                        "month": date(bi.get('date__year'), bi.get('date__month'), 1).strftime("%b") + '.',
                        "total": bi.get('total'),
                    }
                }
            )
        else:
            return Response(
                {
                    "added_files": self.added_files(user),
                    "incomes": in_out.get('total_incomes'),
                    "expenses": in_out.get('total_expenses'),
                    "most_valuable_category": self.most_valuable_category(user),
                    "biggest_spending_month": 'no data'
                }
            )

    @staticmethod
    def added_files(user):
        result = DataFile.objects.filter(user=user).aggregate(total=Count('id'))
        return result['total'] or 0

    @staticmethod
    def income_expenses(user):
        result = UserInOutInfo.objects.filter(user=user).aggregate(
            total_incomes=Sum(
                Case(When(operation_type='income', then=F('amount')), default=0,
                     output_field=DecimalField()
                     )
            ),
            total_expenses=Sum(
                Case(When(operation_type='expense', then=F('amount')), default=0,
                     output_field=DecimalField()
                     )
            )
        )
        return result or 0

    @staticmethod
    def most_valuable_category(user):
        result = (UserInOutInfo.objects.filter(user=user, operation_type='expense')
        .values('tag__tag')
        .annotate(
            tag=F('tag__tag'),
            total=Sum('amount'),
        )).order_by('-total').values('tag', 'amount').first()
        return result or 'no data'

    @staticmethod
    def biggest_spending_month(user):
        result = (UserInOutInfo.objects.filter(user=user, operation_type='expense')
        .values('date__year', 'date__month')
        .annotate(
            total=Sum('amount'),
        )).order_by('-total').first()
        return result or 'no data'

    @action(methods=['get'], detail=False)
    def get_usergraph(self, request):
        user = request.user
        year = date.today().year
        result = (UserInOutInfo.objects
        .filter(user=user, date__year=year)
        .values('date__year', 'date__month')
        .annotate(total_income=Sum(Case(
            When(operation_type='income', then=F('amount')), default=0,
            output_field=DecimalField())), total_expense=Sum(Case(
            When(operation_type='expense', then=F('amount')), default=0,
            output_field=DecimalField()))
        )
        ).order_by('date__year', 'date__month')
        result_list = list(result)
        for i in range(len(result_list)):
            diff = result_list[i]['total_income'] - result_list[i]['total_expense']
            result_list[i]['diff'] = diff

        for i in range(1, len(result_list)):
            prev_dif = result_list[i - 1]['diff']
            current_dif = result_list[i]['diff']

            result_list[i]['diff_absolute'] = current_dif - prev_dif

            if prev_dif != 0:
                result_list[i]['diff_percent'] = round(((current_dif - prev_dif) / prev_dif) * 100, 2)
            else:
                result_list[i]['diff_percent'] = 0

        if result_list:
            result_list[0]['diff_absolute'] = 0
            result_list[0]['diff_percent'] = 0

        return Response(result_list)


class UserFileViewSet(ViewSet):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def add_file(request):
        serializer = FileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data['file']

        data = import_transaction(request.user, validated_data, False)

        if data['status'] == 200 or data['status'] == 206:
            return Response(data)

    @staticmethod
    def list(request):
        files = (
            DataFile.objects.filter(user=request.user)
            .annotate(total_ops=Count("file_link"))
            .values("id", "file_name", "uploaded_at", "total_ops")
        )

        return Response({
            "files": list(files),
            "total_links": sum(f["total_ops"] for f in files)
        })

    @staticmethod
    def delete_file(request):
        file_id = request.data.get('id')
        if file_id and isinstance(file_id, list):
            if DataFile.objects.filter(id__in=file_id).exists():
                count = 0
                for i in file_id:
                    DataFile.objects.get(id=i, user=request.user).delete()
                    count += 1
                if count != len(file_id):
                    return HttpResponseBadRequest()
                return Response({'status': 'success', 'message': f'{count} files was deleted'})
            return Response({'status': 'error', 'message': f'file with id in {file_id} not found'})
        return Response({'status': 'error', 'message': 'id field incorrect, need array with nums'})
