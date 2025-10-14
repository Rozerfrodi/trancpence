from django.urls import path, include
from rest_framework.routers import DefaultRouter
from main.views import *

app_name = 'main'
router = DefaultRouter()
router.register(r'operations', OperationViewSet, basename='main_operation')
urlpatterns = [
	path('', tpshka, name='tpshka'),
	path('', include(router.urls), name='operation_list'),
	path('graph/', GraphViewSet.as_view({'get': 'params'}), name='graph'),
]