from django.test import TestCase # type:ignore
from django.urls import reverse # type:ignore
from rest_framework import status # type:ignore
from rest_framework.test import APIClient # type:ignore
from .models import RentalContract

class RentalContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()  # Usar APIClient para testar views de API
        self.contract_data = {
            "landlord": "0x1234567890123456789012345678901234567890",
            "tenant": "0x0987654321098765432109876543210987654321",
            "rent_amount": 1000.0,
            "deposit_amount": 200.0,
            "private_key": "chave_privada_de_teste"
        }

    def test_create_contract(self):
        url = reverse('create_contract_api')
        response = self.client.post(url, self.contract_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RentalContract.objects.count(), 1)
        self.assertEqual(RentalContract.objects.get().landlord, self.contract_data["landlord"])
        
class SignContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.contract = RentalContract.objects.create(
            landlord="0x1234567890123456789012345678901234567890",
            tenant="0x0987654321098765432109876543210987654321",
            rent_amount=1000.0,
            deposit_amount=200.0,
            contract_address="0xContractAddress"
        )
        self.sign_data = {
            "contract_id": self.contract.id,
            "private_key": "chave_privada_de_teste",
            "user_type": "landlord"
        }

    def test_sign_contract(self):
        url = reverse('sign_contract_api')
        response = self.client.post(url, self.sign_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.contract.refresh_from_db()
        self.assertIsNotNone(self.contract.landlord_signature)

class UrlTests(TestCase):
    def test_contract_list_url(self):
        url = reverse('contract_list')
        self.assertEqual(url, '/api/contracts/')

    def test_create_contract_url(self):
        url = reverse('create_contract')
        self.assertEqual(url, '/api/create/')

    def test_pay_rent_url(self):
        contract_id = 1
        url = reverse('pay_rent', args=[contract_id])
        self.assertEqual(url, f'/api/contracts/{contract_id}/pay_rent/')

    def test_register_payment_url(self):
        contract_id = 1
        url = reverse('register_payment', args=[contract_id])
        self.assertEqual(url, f'/api/contracts/{contract_id}/register_payment/')

    def test_terminate_contract_url(self):
        contract_id = 1
        url = reverse('terminate_contract', args=[contract_id])
        self.assertEqual(url, f'/api/contracts/{contract_id}/terminate/')

    def test_sign_contract_url(self):
        contract_id = 1
        url = reverse('sign_contract', args=[contract_id])
        self.assertEqual(url, f'/api/contracts/{contract_id}/sign/')

    def test_execute_contract_url(self):
        contract_id = 1
        url = reverse('execute_contract', args=[contract_id])
        self.assertEqual(url, f'/api/contracts/{contract_id}/execute/')
