import json
import os
from datetime import date, datetime, timedelta
from unittest.mock import mock_open, patch, MagicMock, Mock

from dateutil.relativedelta import relativedelta  # type: ignore
from django.core.exceptions import ValidationError  # type: ignore
from django.test import TestCase  # type: ignore
from django.urls import reverse  # type: ignore
from django.utils import timezone  # type: ignore
from rest_framework.test import APIClient  # type: ignore
from web3 import Web3  # type: ignore

from contratos_inteligentes.models import (ContractEvent, Payment,
                                           RentalContract, Usuario)
from contratos_inteligentes.utils.check_connection import check_connection
from contratos_inteligentes.utils.load_contract_data import load_contract_data
from contratos_inteligentes.utils.log_contract_event import log_contract_event
from contratos_inteligentes.utils.normalize_address import normalize_address
from web3.providers.eth_tester import EthereumTesterProvider  # type: ignore
from contratos_inteligentes.utils.blockchain_connector import BlockchainConnector

from .utils.load_contract_data import load_contract_data

contract_abi, bytecode = load_contract_data()
os.environ["TEST_ENV"] = "true"

def mock_check_connection():
    # Cria uma instância mock do Web3
    mock_web3 = Mock(spec=Web3)
    mock_web3.is_connected.return_value = True
    mock_web3.eth = Mock()

    # Mock do contrato para responder como se estivesse ativo
    mock_contract = Mock()
    mock_contract.functions.isContractActive.return_value.call.return_value = True
    mock_web3.eth.contract.return_value = mock_contract

    return mock_web3

class ContractAPITestCase(TestCase):
    def setUp(self):
        # Configurações iniciais para os testes
        self.client = APIClient()
        self.create_url = reverse("create_contract")
        self.sign_url = lambda contract_id: reverse("sign_contract", args=[contract_id])
        self.payment_url = lambda contract_id: reverse(
            "register_payment", args=[contract_id]
        )
        self.terminate_url = lambda contract_id: reverse(
            "terminate_contract", args=[contract_id]
        )

        self.contract_data = {
            "landlord": "0x2efc7DFb5c7bbDd221a2060c83ED4C14d062F335",
            "tenant": "0xC7d62268F8700eaF20047EAC54c142408301606d",
            "rent_amount": 1,
            "deposit_amount": 1,
            "start_date": "2024-11-01",
            "end_date": "2024-12-31",
            "contract_duration": 12,
            "private_key_landlord": "0x851e3cf1a6db1937de7ab71ee0ec25607649d87184d6e5cf199ce72c2263c45c",
            "private_key_tenant": "0x5990c131de45024a70bed095da1e58a48972ed815694719b4f251a8b6d59e24b",
            "private_key_random": "0xb64759ae9387aa4f9c08b4ac95e797b02bbce33a7aca2bfd2e8df5ba3f9aaa05",
        }
    
    @patch("contratos_inteligentes.utils.check_connection", side_effect=check_connection)
    def test_create_contract_success(self, mock_to_wei):  # Adicione o argumento mock
        """Teste para verificar a criação de contrato com dados válidos."""
        contract_data = {
            "landlord": self.contract_data["landlord"],
            "tenant": self.contract_data["tenant"],
            "rent_amount": self.contract_data["rent_amount"],
            "deposit_amount": self.contract_data["deposit_amount"],
            "start_date": self.contract_data["start_date"],
            "end_date": self.contract_data["end_date"],
            "contract_duration": self.contract_data["contract_duration"],
            "private_key": self.contract_data["private_key_landlord"],
        }
        response = self.client.post(self.create_url, data=contract_data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertIn("contract_address", response.data)

    def test_create_contract_missing_field(self):
        """Teste para verificar a falha ao criar contrato com campos obrigatórios ausentes."""
        invalid_data = {
            "tenant": self.contract_data["tenant"],
            "rent_amount": self.contract_data["rent_amount"],
            "deposit_amount": self.contract_data["deposit_amount"],
            "start_date": self.contract_data["start_date"],
            "end_date": self.contract_data["end_date"],
            "contract_duration": self.contract_data["contract_duration"],
            "private_key": self.contract_data["private_key_landlord"],
        }
        # O campo 'landlord' está faltando
        response = self.client.post(self.create_url, data=invalid_data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_create_contract_invalid_dates(self):
        invalid_data = self.contract_data.copy()
        invalid_data["start_date"] = "2025-01-01"
        invalid_data["end_date"] = "2024-01-01"  # Data de término anterior à data de início
        invalid_data["private_key"] = self.contract_data["private_key_landlord"]

        response = self.client.post(self.create_url, data=invalid_data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("A data de término deve ser posterior à data de início.", response.data["error"])

    def test_create_contract_with_invalid_dates(self):
        response = self.client.post(
            "/api/create/",
            {
                "landlord": self.contract_data["landlord"],
                "tenant": self.contract_data["tenant"],
                "rent_amount": self.contract_data["rent_amount"],
                "deposit_amount": self.contract_data["deposit_amount"],
                "start_date": "2024-12-01",
                "end_date": "2024-11-01",  # Data de término anterior à data de início
                "contract_duration": self.contract_data["contract_duration"],
                "private_key": self.contract_data["private_key_landlord"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("A data de término deve ser posterior à data de início.", response.data["error"])

    def test_create_contract_missing_fields(self):
        invalid_data = self.contract_data.copy()
        invalid_data.pop("tenant")  # Remover o campo 'tenant'
        response = self.client.post(self.create_url, data=invalid_data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("O campo 'tenant' é obrigatório.", response.data["error"])

    def test_create_contract_invalid_date_format(self):
        invalid_data = {
            "landlord": self.contract_data["landlord"],
            "tenant": self.contract_data["tenant"],
            "rent_amount": self.contract_data["rent_amount"],
            "deposit_amount": self.contract_data["deposit_amount"],
            "start_date": "01-11-2024",  # Formato de data inválido
            "end_date": self.contract_data["end_date"],
            "contract_duration": self.contract_data["contract_duration"],
            "private_key": self.contract_data["private_key_landlord"],
        }
        response = self.client.post(self.create_url, data=invalid_data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Formato de data inválido", response.data["error"])

@patch("contratos_inteligentes.utils.check_connection", side_effect=mock_check_connection)
@patch("contratos_inteligentes.utils.blockchain_connector.Web3", autospec=True)
def test_create_contract_web3_connection_error(self, mock_web3, check_connection):
    """Teste para simular erro de conexão com o Web3 na criação de contrato."""
    
    # Forçar o mock para que a conexão falhe
    mock_web3.return_value.is_connected.return_value = False
    
    # Executar a requisição de criação de contrato
    create_response = self.client.post(
        self.create_url,
        data={
            "landlord": self.contract_data["landlord"],
            "tenant": self.contract_data["tenant"],
            "rent_amount": self.contract_data["rent_amount"],
            "deposit_amount": self.contract_data["deposit_amount"],
            "start_date": self.contract_data["start_date"],
            "end_date": self.contract_data["end_date"],
            "contract_duration": self.contract_data["contract_duration"],
            "private_key": self.contract_data["private_key_landlord"],
        },
        format="json",
    )
    
    # Verificar que o código de status retornado é o esperado para falha de conexão
    self.assertEqual(create_response.status_code, 500, "A conexão com o Web3 deveria ter falhado.")

@patch("contratos_inteligentes.utils.check_connection", side_effect=mock_check_connection)
@patch("contratos_inteligentes.views.smart_contract.functions.isContractActive.call", return_value=True)
def test_sign_contract_as_landlord(self, check_connection, mock_is_contract_active):
    """Teste para assinatura do contrato pelo locador."""
    
    # Criar o contrato
    create_response = self.client.post(
        self.create_url,
        data={
            "landlord": self.contract_data["landlord"],
            "tenant": self.contract_data["tenant"],
            "rent_amount": self.contract_data["rent_amount"],
            "deposit_amount": self.contract_data["deposit_amount"],
            "start_date": self.contract_data["start_date"],
            "end_date": self.contract_data["end_date"],
            "contract_duration": self.contract_data["contract_duration"],
            "private_key": self.contract_data["private_key_landlord"],
        },
        format="json",
    )
    
    # Verificar status de criação
    self.assertEqual(create_response.status_code, 201, f"Erro na criação do contrato: {create_response.data}")
    
    # Confirmação do ID e endereço do contrato
    contract_id = create_response.json().get("id")
    self.assertIsNotNone(contract_id, "O ID do contrato não foi retornado.")
    
    contract_address = create_response.json().get("contract_address")
    self.assertIsNotNone(contract_address, "O endereço do contrato não foi retornado.")
    
    # Assinar como locador
    sign_data = {
        "private_key": self.contract_data["private_key_landlord"],
        "user_type": "landlord",
    }
    sign_response = self.client.post(self.sign_url(contract_id), data=sign_data, format="json")
    self.assertEqual(sign_response.status_code, 200)
    self.assertIn("tx_hash", sign_response.json())

    def test_sign_contract_already_signed(self):
        """Testa se o contrato já assinado não pode ser assinado novamente pelo mesmo usuário."""
        create_response = self.client.post(
            self.create_url,
            data={
                "landlord": self.contract_data["landlord"],
                "tenant": self.contract_data["tenant"],
                "rent_amount": self.contract_data["rent_amount"],
                "deposit_amount": self.contract_data["deposit_amount"],
                "start_date": self.contract_data["start_date"],
                "end_date": self.contract_data["end_date"],
                "contract_duration": self.contract_data["contract_duration"],
                "private_key": self.contract_data["private_key_landlord"],
            },
            format="json",
        )
        contract_id = create_response.json().get("id")

        # Assinar o contrato pela primeira vez
        sign_data = {
            "private_key": self.contract_data["private_key_landlord"],
            "user_type": "landlord",
        }
        first_sign_response = self.client.post(self.sign_url(contract_id), data=sign_data, format="json")
        self.assertEqual(first_sign_response.status_code, 200, "Erro na primeira assinatura do contrato.")

        # Assinar o contrato como inquilino para completá-lo
        tenant_sign_data = {
            "private_key": self.contract_data["private_key_tenant"],
            "user_type": "tenant",
        }
        second_sign_response = self.client.post(self.sign_url(contract_id), data=tenant_sign_data, format="json")
        self.assertEqual(second_sign_response.status_code, 200, "Erro na assinatura do contrato pelo inquilino.")

        # Tentar assinar novamente pelo locador após o contrato já estar completamente assinado
        third_sign_response = self.client.post(self.sign_url(contract_id), data=sign_data, format="json")
        self.assertEqual(third_sign_response.status_code, 403)
        self.assertIn("O contrato já foi assinado por ambas as partes.", third_sign_response.json().get("error", ""))

    def test_sign_contract_invalid_user(self):
        create_response = self.client.post(
            self.create_url,
            data={
                "landlord": self.contract_data["landlord"],
                "tenant": self.contract_data["tenant"],
                "rent_amount": self.contract_data["rent_amount"],
                "deposit_amount": self.contract_data["deposit_amount"],
                "start_date": self.contract_data["start_date"],
                "end_date": self.contract_data["end_date"],
                "contract_duration": self.contract_data["contract_duration"],
                "private_key": self.contract_data["private_key_landlord"],
            },
            format="json",
        )
        contract_id = create_response.json().get("id")

        sign_data = {"private_key": "0xINVALID_PRIVATE_KEY", "user_type": "landlord"}
        response = self.client.post(self.sign_url(contract_id), data=sign_data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertIn("Chave privada inválida.", response.json().get("error", ""))

    def test_sign_contract_not_found(self):
        """Testa se a API retorna 404 ao tentar assinar um contrato que não existe."""
        response = self.client.post(
            self.sign_url(999),
            data={
                "private_key": self.contract_data["private_key_landlord"],
                "user_type": "landlord",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Contrato não encontrado.", response.json().get("error", ""))


    def test_sign_contract_with_invalid_private_key(self):
        create_response = self.client.post(
            self.create_url,
            data={
                "landlord": self.contract_data["landlord"],
                "tenant": self.contract_data["tenant"],
                "rent_amount": self.contract_data["rent_amount"],
                "deposit_amount": self.contract_data["deposit_amount"],
                "start_date": self.contract_data["start_date"],
                "end_date": self.contract_data["end_date"],
                "contract_duration": self.contract_data["contract_duration"],
                "private_key": self.contract_data["private_key_landlord"],
            },
            format="json",
        )
        contract_id = create_response.json().get("id")

        sign_data = {"private_key": "chave_invalida", "user_type": "landlord"}
        response = self.client.post(self.sign_url(contract_id), data=sign_data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Chave privada inválida.", response.json().get("error", ""))

    @patch("contratos_inteligentes.utils.check_connection.check_connection", side_effect=mock_check_connection)
    def test_register_payment(self, mock_check):
        """Teste para registrar um pagamento de aluguel."""
        create_response = self.client.post(
            self.create_url,
            data={
                "landlord": self.contract_data["landlord"],
                "tenant": self.contract_data["tenant"],
                "rent_amount": self.contract_data["rent_amount"],
                "deposit_amount": self.contract_data["deposit_amount"],
                "start_date": self.contract_data["start_date"],
                "end_date": self.contract_data["end_date"],
                "contract_duration": self.contract_data["contract_duration"],
                "private_key": self.contract_data["private_key_landlord"],
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, f"Erro na criação do contrato: {create_response.data}")
        self.assertIn("id", create_response.data, "ID do contrato não retornado após criação.")

        contract_id = create_response.data["id"]
        self.assertIsNotNone(contract_id, "Erro na criação do contrato: ID não encontrado.")
        
        # Assinatura pelo locador
        sign_data_landlord = {
            "private_key": self.contract_data["private_key_landlord"],
            "user_type": "landlord",
        }
        sign_response_landlord = self.client.post(self.sign_url(contract_id), data=sign_data_landlord, format="json")
        self.assertEqual(sign_response_landlord.status_code, 200)

        # Assinatura pelo locatário
        sign_data_tenant = {
            "private_key": self.contract_data["private_key_tenant"],
            "user_type": "tenant",
        }
        sign_response_tenant = self.client.post(self.sign_url(contract_id), data=sign_data_tenant, format="json")
        self.assertEqual(sign_response_tenant.status_code, 200)

        # Dados do pagamento
        payment_data = {
            "private_key": self.contract_data["private_key_tenant"],
            "payment_type": "Aluguel",
            "amount": 1,
        }
        payment_response = self.client.post(self.payment_url(contract_id), data=payment_data, format="json")
        self.assertEqual(payment_response.status_code, 200)
        self.assertIn("tx_hash", payment_response.data)

    def test_register_payment_incorrect_amount(self):
        create_response = self.client.post(
            self.create_url,
            data={
                "landlord": self.contract_data["landlord"],
                "tenant": self.contract_data["tenant"],
                "rent_amount": self.contract_data["rent_amount"],
                "deposit_amount": self.contract_data["deposit_amount"],
                "start_date": self.contract_data["start_date"],
                "end_date": self.contract_data["end_date"],
                "contract_duration": self.contract_data["contract_duration"],
                "private_key": self.contract_data["private_key_landlord"],
            },
            format="json",
        )
        
        self.assertEqual(create_response.status_code, 201, f"Erro na criação do contrato: {create_response.data}")
        self.assertIn("id", create_response.data, "ID do contrato não retornado após criação.")

        contract_id = create_response.data["id"]

        # Assinaturas
        sign_data_landlord = {
            "private_key": self.contract_data["private_key_landlord"],
            "user_type": "landlord",
        }
        self.client.post(self.sign_url(contract_id), data=sign_data_landlord, format="json")

        sign_data_tenant = {
            "private_key": self.contract_data["private_key_tenant"],
            "user_type": "tenant",
        }
        self.client.post(self.sign_url(contract_id), data=sign_data_tenant, format="json")

        incorrect_payment_data = {
            "private_key": self.contract_data["private_key_tenant"],
            "payment_type": "Aluguel",
            "amount": "5000",  # valor diferente do esperado
        }
        payment_response = self.client.post(self.payment_url(contract_id), data=incorrect_payment_data, format="json")
        self.assertEqual(payment_response.status_code, 400)
        self.assertIn("Valor incorreto para Aluguel", payment_response.data["error"])

@patch("contratos_inteligentes.utils.check_connection", side_effect=mock_check_connection)
def test_terminate_contract(self, check_connection):
    """Teste para encerrar o contrato."""

    # Processo de criação e verificação do contrato segue igual
    create_response = self.client.post(
        self.create_url,
        data={
            "landlord": self.contract_data["landlord"],
            "tenant": self.contract_data["tenant"],
            "rent_amount": self.contract_data["rent_amount"],
            "deposit_amount": self.contract_data["deposit_amount"],
            "start_date": self.contract_data["start_date"],
            "end_date": self.contract_data["end_date"],
            "contract_duration": self.contract_data["contract_duration"],
            "private_key": self.contract_data["private_key_landlord"],
        },
        format="json",
    )
    self.assertEqual(create_response.status_code, 201, f"Erro na criação do contrato: {create_response.data}")
    contract_id = create_response.json().get("id")
    self.assertIsNotNone(contract_id, "O ID do contrato não foi retornado.")

    # Simula a assinatura e encerramento do contrato
    sign_data_landlord = {"private_key": self.contract_data["private_key_landlord"], "user_type": "landlord"}
    sign_response_landlord = self.client.post(self.sign_url(contract_id), data=sign_data_landlord, format="json")
    self.assertEqual(sign_response_landlord.status_code, 200)

    sign_data_tenant = {"private_key": self.contract_data["private_key_tenant"], "user_type": "tenant"}
    sign_response_tenant = self.client.post(self.sign_url(contract_id), data=sign_data_tenant, format="json")
    self.assertEqual(sign_response_tenant.status_code, 200)

    # Encerrar o contrato
    terminate_data = {"private_key": self.contract_data["private_key_landlord"]}
    terminate_response = self.client.post(self.terminate_url(contract_id), data=terminate_data, format="json")

    # Verificações de encerramento
    self.assertEqual(terminate_response.status_code, 200, f"Erro ao encerrar o contrato: {terminate_response.data}")
    self.assertEqual(terminate_response.data["message"], "Contrato encerrado com sucesso!")

    def test_terminate_contract_not_signed(self):
        """Teste para verificar a falha ao encerrar um contrato que não foi totalmente assinado."""
        create_response = self.client.post(
            self.create_url,
            data={
                "landlord": self.contract_data["landlord"],
                "tenant": self.contract_data["tenant"],
                "rent_amount": self.contract_data["rent_amount"],
                "deposit_amount": self.contract_data["deposit_amount"],
                "start_date": self.contract_data["start_date"],
                "end_date": self.contract_data["end_date"],
                "contract_duration": self.contract_data["contract_duration"],
                "private_key": self.contract_data["private_key_landlord"],
            },
            format="json",
        )
        contract_id = create_response.data["id"]

        # Tentar encerrar contrato não assinado
        terminate_data = {"private_key": self.contract_data["private_key_landlord"]}
        response = self.client.post(self.terminate_url(contract_id), data=terminate_data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("O contrato precisa ser assinado por ambas as partes", response.data["error"])

    def test_terminate_contract_by_unauthorized_user(self):
        """Testa o encerramento do contrato por um usuário não autorizado."""
        create_response = self.client.post(
            self.create_url,
            data={
                "landlord": self.contract_data["landlord"],
                "tenant": self.contract_data["tenant"],
                "rent_amount": self.contract_data["rent_amount"],
                "deposit_amount": self.contract_data["deposit_amount"],
                "start_date": self.contract_data["start_date"],
                "end_date": self.contract_data["end_date"],
                "contract_duration": self.contract_data["contract_duration"],
                "private_key": self.contract_data["private_key_landlord"],
            },
            format="json",
        )
        contract_id = create_response.data["id"]

        # Tentativa de encerramento pelo usuário não autorizado
        response = self.client.post(
            f"/api/contracts/{contract_id}/terminate/",
            {"private_key": self.contract_data["private_key_random"]},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("Somente o locador ou o inquilino podem encerrar o contrato.", response.data["error"])

    @patch("contratos_inteligentes.utils.check_connection", side_effect=check_connection)
    @patch("contratos_inteligentes.services.contract_service.create_contract", return_value="0x1234567890abcdef1234567890abcdef12345678")
    def test_simular_tempo(self, mock_create_contract, mock_check_connection):
        """Teste para simulação de tempo e renovação de contrato."""
        create_response = self.client.post(
            self.create_url,
            data={
                "landlord": self.contract_data["landlord"],
                "tenant": self.contract_data["tenant"],
                "rent_amount": str(1),
                "deposit_amount": str(2),
                "start_date": self.contract_data["start_date"],
                "end_date": self.contract_data["end_date"],
                "contract_duration": 12,
                "private_key": self.contract_data["private_key_landlord"],
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, 201, f"Erro na criação do contrato: {create_response.json()}")
        contract_id = create_response.json().get("id")
        self.assertIsNotNone(contract_id, "O ID do contrato não foi retornado.")

        # Assinar o contrato
        sign_data_landlord = {"private_key": self.contract_data["private_key_landlord"], "user_type": "landlord"}
        self.client.post(self.sign_url(contract_id), data=sign_data_landlord, format="json")
        sign_data_tenant = {"private_key": self.contract_data["private_key_tenant"], "user_type": "tenant"}
        self.client.post(self.sign_url(contract_id), data=sign_data_tenant, format="json")

        # Simular passagem de tempo
        original_end_date = datetime.strptime(self.contract_data["end_date"], "%Y-%m-%d").date()
        simulated_date = (original_end_date + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = self.client.post(
            f"/api/contracts/{contract_id}/simular_tempo/",
            data={"simulated_date": simulated_date, "private_key": self.contract_data["private_key_landlord"]},
            format="json",
        )
        
        # Verificação
        self.assertEqual(response.status_code, 200)
        self.assertIn("Tempo simulado e contrato atualizado.", response.json().get("message", ""))

        # Validar data atualizada do contrato
        rental_contract = RentalContract.objects.get(id=contract_id)
        expected_new_end_date = original_end_date + relativedelta(months=self.contract_data["contract_duration"])
        self.assertEqual(rental_contract.end_date, expected_new_end_date)
        self.assertEqual(rental_contract.simulated_time, datetime.strptime(simulated_date, "%Y-%m-%d").date())

class RentalContractTests(TestCase):
    def setUp(self):
        self.contract = RentalContract.objects.create(
            landlord="0x1234567890abcdef1234567890abcdef12345678",
            tenant="0xabcdef1234567890abcdef1234567890abcdef12",
            rent_amount=1000,
            deposit_amount=2000,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1),
            rent_due_date=date(2024, 2, 1),
            contract_duration=12,
        )
        self.contract.contract_address = "0xabcdef1234567890abcdef1234567890abcdef12"
        self.contract.save()

    def test_valid_rental_contract(self):
        self.contract.clean()
        self.contract.save()
        self.assertEqual(RentalContract.objects.count(), 1)

    def test_invalid_contract_address_length(self):
        self.contract.contract_address = "0x123"
        with self.assertRaises(ValidationError):
            self.contract.clean()

    def test_end_date_before_start_date(self):
        self.contract.end_date = date(2023, 12, 31)
        with self.assertRaises(ValidationError):
            self.contract.clean()

    def test_negative_rent_amount(self):
        self.contract.rent_amount = -100
        with self.assertRaises(ValidationError):
            self.contract.clean()

    def test_is_fully_signed(self):
        self.contract.landlord_signature = "assinatura_locador"
        self.contract.tenant_signature = "assinatura_inquilino"
        self.assertTrue(self.contract.is_fully_signed())

class UtilsTests(TestCase):
    def setUp(self):
        self.contract = RentalContract.objects.create(
            landlord="0x1234567890abcdef1234567890abcdef12345678",
            tenant="0xabcdef1234567890abcdef1234567890abcdef12",
            rent_amount=1,
            deposit_amount=2,
            start_date="2024-01-01",
            end_date="2025-01-01",
            rent_due_date="2024-02-01",
            contract_duration=12,
            contract_address="0xabcdef1234567890abcdef1234567890abcdef12",
        )

    def test_normalize_address_valid(self):
        address = "0xabcdef1234567890abcdef1234567890abcdef12"
        checksum_address = normalize_address(address)
        self.assertEqual(checksum_address, Web3.to_checksum_address(address))

    def test_normalize_address_invalid(self):
        invalid_address = "0x123"
        with self.assertRaises(ValueError):
            normalize_address(invalid_address)

    def test_log_contract_event(self):
        event_type = "sign"
        user_address = "0xabcdef1234567890abcdef1234567890abcdef12"
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        event_data = {"details": "Contrato assinado"}

        log_contract_event(self.contract, event_type, user_address, tx_hash, event_data)

        event = ContractEvent.objects.get(contract=self.contract)
        self.assertEqual(event.event_type, event_type)
        self.assertEqual(event.user_address, user_address)
        self.assertEqual(event.transaction_hash, tx_hash)
        self.assertEqual(event.event_data, event_data)

    def setUp(self):
        # Criação de um contrato para os testes
        self.contract = RentalContract.objects.create(
            landlord="0x1234567890abcdef1234567890abcdef12345678",
            tenant="0xabcdef1234567890abcdef1234567890abcdef12",
            rent_amount=1000,
            deposit_amount=2000,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1),
            rent_due_date=date(2024, 2, 1),
            contract_duration=12,
            contract_address="0xabcdef1234567890abcdef1234567890abcdef12",
        )

    @patch("contratos_inteligentes.utils.blockchain_connector.BlockchainConnector.connect", side_effect=Exception("Não conectado à rede Ethereum"))
    def test_check_connection_failure(self, mock_connect):
        """Verifica se `check_connection` falha corretamente."""
        with self.assertRaises(Exception) as context:
            check_connection()
        self.assertIn("Não conectado à rede Ethereum", str(context.exception))

    def test_normalize_address_empty_string(self):
        """Testa se uma string vazia gera um ValueError."""
        with self.assertRaises(ValueError):
            normalize_address("")

    def test_normalize_address_none(self):
        with self.assertRaises(ValueError) as context:
            normalize_address(None)
        self.assertEqual(str(context.exception), "Endereço não pode ser None ou vazio.")

    @patch.dict(os.environ, {"TEST_ENV": "false", "GANACHE_URL": "http://invalid-url"})
    def test_check_connection_invalid_url(self):
        """Verifica se uma exceção é levantada para uma URL inválida."""
        connector = BlockchainConnector()
        with self.assertRaises(Exception) as context:
            connector.connect()
        self.assertIn("Não conectado à rede Ethereum", str(context.exception))

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_contract_data_file_not_found(self, mock_open):
        """Testa se um erro ocorre quando o arquivo não é encontrado."""
        with self.assertRaises(FileNotFoundError):
            load_contract_data()

    @patch("builtins.open", new_callable=mock_open, read_data="not a valid json")
    def test_load_contract_data_invalid_json(self, mock_open):
        """Testa se um erro ocorre quando o JSON é inválido."""
        with self.assertRaises(json.JSONDecodeError):
            load_contract_data()

    ######################## LOG DE EVENTOS ########################
    def test_log_contract_event_success(self):
        event_type = "create"
        user_address = "0xabcdef1234567890abcdef1234567890abcdef12"
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        event_data = {"details": "Contrato criado"}

        log_contract_event(self.contract, event_type, user_address, tx_hash, event_data)

        event = ContractEvent.objects.get(contract=self.contract)
        self.assertEqual(event.event_type, event_type)
        self.assertEqual(event.user_address, user_address)
        self.assertEqual(event.transaction_hash, tx_hash)
        self.assertEqual(event.event_data, event_data)

    def test_log_contract_event_with_none_contract(self):
        """Testa se a função gera um ValueError quando o contrato é None."""
        with self.assertRaises(ValueError) as context:
            log_contract_event(
                None, "create", "0xabcdef1234567890abcdef1234567890abcdef12"
            )
        self.assertEqual(str(context.exception), "O contrato não pode ser None.")

    def test_log_contract_event_with_empty_event_type(self):
        """Testa se a função gera um ValueError quando o tipo de evento é vazio."""
        with self.assertRaises(ValueError) as context:
            log_contract_event(
                self.contract, "", "0xabcdef1234567890abcdef1234567890abcdef12"
            )
        self.assertEqual(str(context.exception), "O tipo de evento não pode ser vazio.")

    def test_log_contract_event_with_empty_user_address(self):
        """Testa se a função gera um ValueError quando o endereço do usuário é vazio."""
        with self.assertRaises(ValueError) as context:
            log_contract_event(self.contract, "create", "")
        self.assertEqual(
            str(context.exception), "O endereço do usuário não pode ser vazio."
        )

    def test_valid_address(self):
        valid_address = "0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
        result = normalize_address(valid_address)
        self.assertEqual(result, Web3.to_checksum_address(valid_address))

    def test_invalid_address_format(self):
        invalid_address = "0xInvalidAddress12345"
        with self.assertRaises(ValueError) as context:
            normalize_address(invalid_address)
        self.assertIn("Endereço inválido", str(context.exception))

    def test_empty_address(self):
        empty_address = ""
        with self.assertRaises(ValueError) as context:
            normalize_address(empty_address)
        self.assertIn("Endereço não pode ser None ou vazio", str(context.exception))

    def test_none_address(self):
        none_address = None
        with self.assertRaises(ValueError) as context:
            normalize_address(none_address)
        self.assertIn("Endereço não pode ser None ou vazio", str(context.exception))

    def test_address_with_incorrect_length(self):
        short_address = "0x12345"
        with self.assertRaises(ValueError) as context:
            normalize_address(short_address)
        self.assertIn("Endereço inválido", str(context.exception))

        long_address = "0x" + "1" * 100
        with self.assertRaises(ValueError) as context:
            normalize_address(long_address)
        self.assertIn("Endereço inválido", str(context.exception))

class RentalContractModelTest(TestCase):
    def setUp(self):
        self.valid_contract_data = {
            "landlord": "0x1234567890123456789012345678901234567890",
            "tenant": "0x0987654321098765432109876543210987654321",
            "rent_amount": 1.00,
            "deposit_amount": 2.00,
            "contract_address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=30),
            "contract_duration": 6,
        }

    def test_valid_rental_contract(self):
        contract = RentalContract(**self.valid_contract_data)
        try:
            contract.full_clean()
        except ValidationError:
            self.fail("Valid RentalContract data raised ValidationError unexpectedly!")

    def test_invalid_contract_address_length(self):
        invalid_data = self.valid_contract_data.copy()
        invalid_data["contract_address"] = "0x12345"
        contract = RentalContract(**invalid_data)
        with self.assertRaises(ValidationError):
            contract.full_clean()

    def test_end_date_before_start_date(self):
        invalid_data = self.valid_contract_data.copy()
        invalid_data["end_date"] = invalid_data["start_date"] - timedelta(days=1)
        contract = RentalContract(**invalid_data)
        with self.assertRaises(ValidationError):
            contract.full_clean()

    def test_negative_rent_amount(self):
        invalid_data = self.valid_contract_data.copy()
        invalid_data["rent_amount"] = -1000.00
        contract = RentalContract(**invalid_data)
        with self.assertRaises(ValidationError):
            contract.full_clean()

    def test_zero_deposit_amount(self):
        invalid_data = self.valid_contract_data.copy()
        invalid_data["deposit_amount"] = -100.00
        contract = RentalContract(**invalid_data)
        with self.assertRaises(ValidationError):
            contract.full_clean()

    def test_is_fully_signed(self):
        contract = RentalContract(**self.valid_contract_data)
        self.assertFalse(contract.is_fully_signed())
        contract.landlord_signature = "valid_signature"
        contract.tenant_signature = "valid_signature"
        self.assertTrue(contract.is_fully_signed())

    def test_is_contract_active(self):
        contract = RentalContract(**self.valid_contract_data)
        self.assertTrue(contract.is_contract_active())

class UserModelTest(TestCase):
    def test_invalid_wallet_address_length(self):
        user = Usuario(
            name="John Doe",
            email="john@example.com",
            wallet_address="0x12345",
            is_landlord=True,
        )
        with self.assertRaises(ValidationError):
            user.full_clean()

class PaymentModelTest(TestCase):
    def setUp(self):
        self.contract = RentalContract.objects.create(
            **{
                "landlord": "0x1234567890123456789012345678901234567890",
                "tenant": "0x0987654321098765432109876543210987654321",
                "rent_amount": 1.00,
                "deposit_amount": 2.00,
                "contract_address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
                "start_date": date.today(),
                "end_date": date.today() + timedelta(days=30),
                "contract_duration": 6,
            }
        )

    def test_payment_creation(self):
        payment = Payment(
            contract=self.contract,
            amount=1.00,
            payment_type="rent",
            transaction_hash="0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdef",
        )
        try:
            payment.full_clean()
        except ValidationError:
            self.fail("Valid Payment data raised ValidationError unexpectedly!")

class BlockchainConnectorTests(TestCase):

    @patch.dict(os.environ, {"TEST_ENV": "true"})
    def test_connect_in_test_environment(self):
        """Verifica a conexão com EthereumTesterProvider em ambiente de teste."""
        connector = BlockchainConnector()
        web3_instance = connector.connect()

        self.assertIsNotNone(web3_instance)
        self.assertTrue(web3_instance.is_connected())
        self.assertEqual(type(web3_instance.provider), Web3.EthereumTesterProvider)

    @patch.dict(os.environ, {"TEST_ENV": "false", "GANACHE_URL": "http://invalid-url"})
    def test_connect_with_invalid_url(self):
        """Verifica se uma exceção é levantada para uma URL inválida."""
        connector = BlockchainConnector()
        with self.assertRaises(Exception) as context:
            connector.connect()

        self.assertIn("Não conectado à rede Ethereum", str(context.exception))
