from django.urls import path
from . import views  # Importa as views do app

urlpatterns = [
    path('api/contracts/', views.contract_list_api, name='contract_list'),
    path('api/create/', views.create_contract_api, name='create_contract'),
    path('api/pay_rent/', views.pay_rent_api, name='pay_rent'),
    path('api/register_payment/', views.register_payment_api, name='pay_deposit'),
    path('api/terminate/', views.terminate_contract_api, name='terminate_contract'),
    path('api/sign_contract/', views.sign_contract_api, name='sign_contract'),
    path('api/execute_contract/', views.execute_contract_api, name='sign_contract'),
]