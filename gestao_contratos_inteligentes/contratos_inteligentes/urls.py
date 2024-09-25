from django.urls import path
from . import views  # Importa as views do app

urlpatterns = [
    path('create/', views.create_contract, name='create_contract'),
    path('contracts/', views.contract_list, name='contract_list'),
]
