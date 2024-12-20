from django.urls import path  # type: ignore
from . import views

urlpatterns = [
    path("api/contracts/", views.contract_list_api, name="contract_list"),
    path("api/create/", views.create_contract_api, name="create_contract"),
    path(
        "api/contracts/<int:contract_id>/register_payment/",
        views.register_payment_api,
        name="register_payment",
    ),
    path(
        "api/contracts/<int:contract_id>/terminate/",
        views.terminate_contract_api,
        name="terminate_contract",
    ),
    path(
        "api/contracts/<int:contract_id>/sign/",
        views.sign_contract_api,
        name="sign_contract",
    ),
    path(
        "api/contracts/<int:contract_id>/events/",
        views.contract_events_api,
        name="contract_events",
    ),
    path("api/users/", views.fetch_users, name="fetch_users"),
    path("api/pending_contracts/", views.get_pending_contracts, name="get_pending_contracts"),
    path(
        "api/contracts/<int:contract_id>/simular_tempo/",
        views.simular_tempo,
        name="simular_tempo",
    ),
    path('api/login/', views.login, name='login'),
    path("api/get_landlord_address/", views.get_landlord_address, name="get_landlord_address"),
    # path('api/contracts/<int:contract_id>/test_contract_functions/', views.test_contract_functions, name='test_contract_functions'),
]
