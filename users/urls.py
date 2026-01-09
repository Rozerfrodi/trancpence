from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from users.views import *
app_name = 'users'

router = DefaultRouter()
router.register('auth/users', CustomUserViewSet, basename='user')
urlpatterns = [
	re_path(r'^auth/', include('djoser.urls.authtoken')),
	path('', include(router.urls)),
	path('users/files/', UserFileViewSet.as_view({'post': 'add_file', 'get':'list', 'delete':'delete_file'}), name='user_files'),
	path('users/logs/', UserLogsViewSet.as_view({'post':'post', 'delete': 'del_logs', 'get':'list'}), name='user_logs'),
	path('compare/', CompareViewSet.as_view({'post': 'post'}), name='compare'),
	path('download_example/', get_example_file, name='download_example'),
]