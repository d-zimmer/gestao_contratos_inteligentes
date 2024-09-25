from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_contract, name='create_contract'),
    path('contracts/', views.contract_list, name='contract_list'),
]
