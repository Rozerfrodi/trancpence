from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from djoser.views import UserViewSet
from django.contrib.auth import get_user_model
from djoser import utils
from django.http import HttpResponse, HttpResponseNotFound, FileResponse
from django.contrib.auth.tokens import default_token_generator
from .models import *
from users.serializers import *
import os
import trancpence.settings as settings

User = get_user_model()


def get_example_file(request):
	file_path = os.path.join(settings.BASE_DIR, 'files', 'example.xlsx')
	return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='example.xlsx')


class CustomUserViewSet(UserViewSet):
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

		return HttpResponse(
			{'detail': 'Email successful changed', 'email': user.email}
		)


@action(methods=['post'], detail=False)
def activate_user_redirect(request, uid, token):
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
