from django.urls import path, include
from main.views import *
from trancpence.my_routs import MyRouter

app_name = 'main'

router = MyRouter()
router.register(r'operations', OperationViewSet, basename='main_operation')
urlpatterns = [
	path('', tpshka, name='tpshka'),
	path('', include(router.urls), name='operation_list'),
	path('graph/', GraphViewSet.as_view({'post': 'params'}), name='graph'),
	path('tags/', GetTagsAPIView.as_view({'get': 'list'}), name='tags'),
	path('graph_ops/', DetailViewSet.as_view({'post': 'params'}), name='graph_ops'),
]