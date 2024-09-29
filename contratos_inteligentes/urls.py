from django.urls import path
from . import views  # Importa as views do app

urlpatterns = [
    path('api/contracts/', views.contract_list, name='contract_list'),
    path('api/create/', views.create_contract, name='create_contract'),
    path('api/pay_rent/', views.pay_rent, name='pay_rent'),
    path('api/register_payment/', views.register_payment, name='pay_deposit'),
    path('api/terminate/', views.terminate_contract, name='terminate_contract'),
    path('api/sign_contract/', views.sign_contract, name='sign_contract'),
    path('api/execute_contract/', views.execute_contract, name='sign_contract'),
]