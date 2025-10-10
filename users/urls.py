from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from users.views import *
app_name = 'users'

router = DefaultRouter()
router.register('auth/users', CustomUserViewSet, basename='user')

urlpatterns = [
	path('auth/', include('djoser.urls')),
	re_path(r'^auth/', include('djoser.urls.authtoken')),
	path('', include(router.urls)),
	path('activate/<str:uid>/<str:token>/', activate_user_redirect, name='activate'),
]