from django.urls import path, include, re_path
from rest_framework import routers
from rest_framework.routers import DefaultRouter

from loan.views import *
from trancpence.my_routs import *

app_name = 'loan'
router = DefaultRouter()
router.register('loan', LoanCRUDView, basename='loan')
urlpatterns = [
    path('', include(router.urls), name='loan_create'),
]