from django.urls import path, include
from rest_framework.routers import DefaultRouter
from main.views import *

app_name = 'main'
router = DefaultRouter()
router.register(r'main', OperationViewSet, basename='main_operation')
urlpatterns = [
	path('', tpshka, name='tpshka'),
	path('operations/', include(router.urls)),
	path('graph/', GraphViewSet.as_view({'get': 'list'}), name='graph'),
]