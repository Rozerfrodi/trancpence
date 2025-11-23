from datetime import date
from django.db.models import Count, Case, Sum, F, When, DecimalField
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from djoser.views import UserViewSet
from django.contrib.auth import get_user_model
from djoser import utils
from django.http import HttpResponse, HttpResponseNotFound, FileResponse, HttpResponseBadRequest
from django.contrib.auth.tokens import default_token_generator
from rest_framework.response import Response
from .models import *
from users.serializers import *
from rest_framework.viewsets import ViewSet, ModelViewSet
import os
import trancpence.settings as settings

User = get_user_model()


def get_example_file(request):
	file_path = os.path.join(settings.BASE_DIR, 'files', 'example.xlsx')
	return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='example.xlsx')


class CustomUserViewSet(UserViewSet, ViewSet):

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

	def added_files(self, user):
		result = DataFile.objects.filter(user=user).aggregate(total=Count('id'))
		return result['total'] or 0

	def income_expenses(self, user):
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

	def most_valuable_category(self, user):
		result = (UserInOutInfo.objects.filter(user=user, operation_type='expense')
		.values('tag__tag')
		.annotate(
			tag = F('tag__tag'),
			total=Sum('amount'),
		)).order_by('-total').values('tag', 'amount').first()
		return result or 'no data'

	def biggest_spending_month(self, user):
		result = (UserInOutInfo.objects.filter(user=user, operation_type='expense')
		.values('date__year', 'date__month')
		.annotate(
			total=Sum('amount'),
		)).order_by('-total').first()
		return result or 'no data'

class UserFileViewSet(ViewSet):
	permission_classes = (IsAuthenticated,)

	def add_file(self, request):
		serializer = FileSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		validated_data = serializer.validated_data['file']

		data = import_transaction(request.user, validated_data, False)

		if data['status'] == 200 or data['status'] == 206:
			return Response(data)

	def list(self, request):
		files = (
			DataFile.objects.filter(user=request.user)
			.annotate(total_ops=Count("file_link"))
			.values("id", "file_name", "uploaded_at", "total_ops")
		)

		return Response({
			"files": list(files),
			"total_links": sum(f["total_ops"] for f in files)
		})


	def delete_file(self, request):
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