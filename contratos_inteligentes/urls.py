from django.urls import path
from . import views  

urlpatterns = [
    path('api/contracts/', views.contract_list_api, name='contract_list'),  # GET para listar, POST para criar
    path('api/create/', views.create_contract_api, name='create_contract'),  # URL para criação de contrato
    path('api/contracts/<int:contract_id>/pay_rent/', views.pay_rent_api, name='pay_rent'),  # Pagamento de aluguel
    path('api/contracts/<int:contract_id>/register_payment/', views.register_payment_api, name='register_payment'),  # Registrar pagamento (aluguel ou depósito)
    path('api/contracts/<int:contract_id>/terminate/', views.terminate_contract_api, name='terminate_contract'),  # Encerrar contrato
    path('api/contracts/<int:contract_id>/sign/', views.sign_contract_api, name='sign_contract'),  # Assinar contrato
    path('api/contracts/<int:contract_id>/execute/', views.execute_contract_api, name='execute_contract'),  # Executar contrato
    path('api/contracts/<int:contract_id>/events/', views.contract_events_api, name='contract_events'),  # Nova rota para eventos
]
