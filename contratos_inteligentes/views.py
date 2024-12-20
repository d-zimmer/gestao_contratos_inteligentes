from datetime import datetime
import json
import os
import traceback
import pytz # type:ignore
from decimal import Decimal 
from cryptography.fernet import Fernet, InvalidToken # type:ignore
import time

from dateutil.relativedelta import relativedelta  # type:ignore
from django.views.decorators.csrf import csrf_exempt # type: ignore
from django.contrib.auth.models import User  # type: ignore
from django.http import JsonResponse  # type:ignore
from django.shortcuts import get_object_or_404  # type:ignore
from django.utils import timezone  # type:ignore
from dotenv import load_dotenv  # type:ignore
from rest_framework import status  # type:ignore
from rest_framework.decorators import api_view  # type:ignore
from rest_framework.response import Response  # type:ignore
from web3 import Account, Web3  # type:ignore
from cryptography.fernet import Fernet # type: ignore

from .serializers import RentalContractSerializer
from .models import ContractEvent, ContractTermination, Payment, RentalContract, Usuario
from .utils.check_connection import check_connection
from .utils.tratar_data import tratar_data
from .utils.load_contract_data import load_contract_data
from .utils.log_contract_event import log_contract_event
from .utils.normalize_address import normalize_address

contract_abi, bytecode = load_contract_data()

# global_contract_address = Web3.to_checksum_address("0x5fbdb2315678afecb367f032d93f642f64180aa3")
# global_contract = web3.eth.contract(address=global_contract_address, abi=contract_abi)

# def encrypt_key(key):
#     try:
#         fernet = Fernet(settings.ENCRYPTION_KEY)
#         return fernet.encrypt(key.encode()).decode()
#     except Exception as e:
#         raise ValueError(f"Erro ao criptografar a chave: {str(e)}")

# def decrypt_key(encrypted_key):
#     try:
#         fernet = Fernet(settings.ENCRYPTION_KEY)
#         return fernet.decrypt(encrypted_key.encode()).decode()
#     except InvalidToken:
#         raise ValueError("Token inválido para descriptografia.")
#     except Exception as e:
#         raise ValueError(f"Erro ao descriptografar a chave: {str(e)}")

@api_view(["POST"])
def create_contract_api(request):
    try:
        web3 = check_connection()
    except Exception as e:
        return Response(
            {"error": "Falha na conexão com a rede Ethereum: " + str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    required_fields = [
        "landlord",
        "tenant",
        "rent_amount",
        "deposit_amount",
        "start_date",
        "end_date",
        "private_key",
    ]

    for field in required_fields:
        if not request.data.get(field):
            return Response(
                {"error": f"O campo '{field}' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        landlord = normalize_address(request.data["landlord"])
        tenant = normalize_address(request.data["tenant"])
        rent_amount = int(request.data["rent_amount"])
        deposit_amount = int(request.data["deposit_amount"])
        start_date = int(request.data["start_date"])  # Deve ser inteiro
        end_date = int(request.data["end_date"])      # Deve ser inteiro
        private_key = request.data["private_key"]

        if end_date <= start_date:
            return Response(
                {"error": "A data de término deve ser posterior à data de início."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contract_duration = (end_date - start_date) // 60  # Duração em minutos
        if contract_duration <= 0:
            return Response(
                {"error": "A duração do contrato deve ser maior que zero."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except ValueError as e:
        return Response(
            {"error": f"Erro ao processar os dados: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": f"Erro inesperado: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        account = web3.eth.account.from_key(private_key)
    except ValueError:
        return Response(
            {"error": "Chave privada inválida."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    smart_contract = web3.eth.contract(abi=contract_abi, bytecode=bytecode)
    try:
        transaction = smart_contract.constructor(
            tenant,
            rent_amount,
            deposit_amount,
            start_date,
            end_date,
        ).build_transaction(
            {
                "from": account.address,
                "nonce": web3.eth.get_transaction_count(account.address),
                "gas": 3000000,
                "gasPrice": web3.to_wei("20", "gwei"),
            }
        )

        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        new_contract_address = tx_receipt.contractAddress

        if not new_contract_address:
            return Response(
                {"error": "Falha ao obter o endereço do contrato na blockchain"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        new_contract = RentalContract.objects.create(
            landlord=landlord,
            tenant=tenant,
            rent_amount=rent_amount,
            deposit_amount=deposit_amount,
            contract_address=new_contract_address,
            status="pending",
            start_date=datetime.fromtimestamp(start_date),  # Converter para datetime
            end_date=datetime.fromtimestamp(end_date), 
            contract_duration=contract_duration,
        )

        return Response(
            {
                "message": "Contrato criado com sucesso!",
                "tx_hash": tx_hash.hex(),
                "contract_address": new_contract_address,
                "id": new_contract.id,
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def sign_contract_api(request, contract_id):
    try:
        if not isinstance(request.data, dict):
            return JsonResponse({"error": "Dados da requisição inválidos."}, status=400)

        rental_contract = RentalContract.objects.filter(id=contract_id).first()
        if not rental_contract:
            return JsonResponse({"error": "Contrato não encontrado."}, status=404)

        private_key = request.data.get("private_key")
        user_type = request.data.get("user_type")

        if not private_key or not user_type:
            return JsonResponse(
                {"error": "Chave privada e tipo de usuário são obrigatórios."}, status=400
            )

        web3 = check_connection()

        account_to_sign = web3.eth.account.from_key(private_key)

        landlord = normalize_address(rental_contract.landlord)
        tenant = normalize_address(rental_contract.tenant)

        smart_contract = web3.eth.contract(
            address=Web3.to_checksum_address(rental_contract.contract_address),
            abi=contract_abi,
        )

        contract_code = web3.eth.get_code(Web3.to_checksum_address(rental_contract.contract_address))
        if contract_code == b"":
            return JsonResponse({"error": "Contrato não implantado na blockchain."}, status=404)

        if smart_contract.functions.isFullySigned().call():
            rental_contract.status = "active"
            rental_contract.save()
            return JsonResponse({"error": "O contrato já foi assinado por ambas as partes."}, status=403)

        if not smart_contract.functions.isContractActive().call():
            return JsonResponse({"error": "O contrato já foi encerrado e não pode ser assinado."}, status=403)

        if user_type == "landlord" and account_to_sign.address.lower() != landlord.lower():
            return JsonResponse({"error": "Apenas o locador pode assinar como 'landlord'."}, status=403)

        if user_type == "tenant" and account_to_sign.address.lower() != tenant.lower():
            return JsonResponse({"error": "Apenas o inquilino pode assinar como 'tenant'."}, status=403)

        nonce = web3.eth.get_transaction_count(account_to_sign.address)
        transaction = smart_contract.functions.signAgreement().build_transaction(
            {
                "from": account_to_sign.address,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": web3.to_wei("20", "gwei"),
            }
        )

        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt["status"] != 1:
            return JsonResponse({"error": "Falha na execução da transação."}, status=500)

        if user_type == "landlord":
            rental_contract.landlord_signature = account_to_sign.address
        elif user_type == "tenant":
            rental_contract.tenant_signature = account_to_sign.address

        if smart_contract.functions.isFullySigned().call():
            rental_contract.status = "active"
        
        rental_contract.save()

        ContractEvent.objects.create(
            contract=rental_contract,
            event_type="sign",
            user_address=account_to_sign.address,
            event_data={"tx_hash": tx_hash.hex(), "user_type": user_type},
            transaction_hash=tx_hash.hex(),
        )

        return JsonResponse(
            {
                "message": "Contrato assinado com sucesso!",
                "tx_hash": tx_hash.hex(),
                "status": rental_contract.status,
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse({"error": f"Erro inesperado: {str(e)}"}, status=500)

@api_view(["POST"])
def register_payment_api(request, contract_id):
    try:
        web3 = check_connection()
        rental_contract = get_object_or_404(RentalContract, id=contract_id)
        private_key = request.data.get("private_key")
        payment_type = request.data.get("payment_type")
        amount = request.data.get("amount")

        if not amount or int(amount) <= 0:
            return Response({"error": "Valor do pagamento inválido."}, status=400)

        try:
            account_to_pay = web3.eth.account.from_key(private_key)
        except ValueError:
            return Response({"error": "Chave privada inválida."}, status=400)

        if (
            account_to_pay.address.lower() != rental_contract.landlord.lower()
            and account_to_pay.address.lower() != rental_contract.tenant.lower()
        ):
            return Response(
                {
                    "error": "Somente o locador ou o inquilino podem registrar pagamentos."
                },
                status=403,
            )

        smart_contract = web3.eth.contract(
            address=Web3.to_checksum_address(rental_contract.contract_address),
            abi=contract_abi,
        )

        try:
            contract_state = smart_contract.functions.getContractState().call()
        except Exception as e:
            return Response(
                {"error": f"Erro ao obter estado do contrato: {str(e)}"}, status=500
            )

        if payment_type == "Aluguel":
            tx_function = smart_contract.functions.payRent()
            expected_amount = smart_contract.functions.getRentAmount().call()
        elif payment_type == "Depósito":
            tx_function = smart_contract.functions.payDeposit()
            expected_amount = smart_contract.functions.getDepositAmount().call()
        else:
            return Response({"error": "Tipo de pagamento inválido."}, status=400)

        if int(amount) != expected_amount:
            return Response(
                {
                    "error": f"Valor incorreto para {payment_type}. Esperado: {expected_amount} Wei, Recebido: {amount} Wei"
                },
                status=400,
            )

        try:
            tx = tx_function.build_transaction(
                {
                    "from": account_to_pay.address,
                    "value": int(amount),
                    "nonce": web3.eth.get_transaction_count(account_to_pay.address),
                    "gas": 200000,
                    "gasPrice": web3.to_wei("20", "gwei"),
                }
            )

            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            if tx_receipt["status"] == 1:
                Payment.objects.create(
                    contract=rental_contract,
                    amount=amount,
                    payment_type="rent" if payment_type == "Aluguel" else "deposit",
                    transaction_hash=tx_hash.hex(),
                    is_verified=True,
                )

                # Registrar o evento de pagamento
                ContractEvent.objects.create(
                    contract=rental_contract,
                    event_type=(
                        "pay_rent" if payment_type == "Aluguel" else "pay_deposit"
                    ),
                    event_data={
                        "tx_hash": tx_hash.hex(),
                        "from_address": account_to_pay.address,
                        "amount": amount,
                    },
                    transaction_hash=tx_hash.hex(),
                    user_address=account_to_pay.address,
                )

                return Response(
                    {
                        "message": f"Pagamento de {payment_type} registrado com sucesso!",
                        "tx_hash": tx_hash.hex(),
                    },
                    status=200,
                )
            else:
                return Response(
                    {"error": "Falha na transação de pagamento."}, status=500
                )

        except Exception as e:
            return Response(
                {"error": f"Erro ao registrar pagamento: {str(e)}"}, status=500
            )

    except Exception as e:
        return Response(
            {
                "error": f"Erro ao processar pagamento: {str(e)}",
                "traceback": traceback.format_exc(),
            },
            status=500,
        )

@api_view(["GET"])
def contract_list_api(request):
    tenant = request.query_params.get("tenant", None)
    contract_status = request.query_params.get("status", None)

    contracts = RentalContract.objects.all()

    # Filtrar pelo tenant (inquilino)
    if tenant:
        contracts = contracts.filter(tenant=tenant)

    # Filtrar pelo status do contrato
    if contract_status:
        contracts = contracts.filter(status=contract_status)

    # Formatar os dados dos contratos como no 'contract_list_api'
    contracts_data = [
        {
            "id": contract.id,
            "landlord": contract.landlord,
            "tenant": contract.tenant,
            "rent_amount": str(contract.rent_amount),
            "deposit_amount": str(contract.deposit_amount),
            "start_date": str(contract.start_date),
            "end_date": str(contract.end_date),
            "contract_address": contract.contract_address,
            "status": contract.status,
            "created_at": contract.created_at,
        }
        for contract in contracts
    ]
    return Response(contracts_data, status=status.HTTP_200_OK)

@api_view(["POST"])
def terminate_contract_api(request, contract_id):
    rental_contract = get_object_or_404(RentalContract, id=contract_id)
    private_key = request.data.get("private_key")

    web3 = check_connection()

    try:
        account_to_terminate = web3.eth.account.from_key(private_key)
    except ValueError:
        return Response({"error": "Chave privada inválida."}, status=400)

    if (
        account_to_terminate.address.lower() != rental_contract.landlord.lower()
        and account_to_terminate.address.lower() != rental_contract.tenant.lower()
    ):
        return Response(
            {"error": "Somente o locador ou o inquilino podem encerrar o contrato."},
            status=403,
        )

    if not rental_contract.is_fully_signed():
        return Response(
            {
                "error": "O contrato precisa ser assinado por ambas as partes antes de ser encerrado."
            },
            status=400,
        )

    smart_contract = web3.eth.contract(
        address=Web3.to_checksum_address(rental_contract.contract_address),
        abi=contract_abi,
    )

    try:
        tx = smart_contract.functions.terminateContract().build_transaction(
            {
                "from": account_to_terminate.address,
                "nonce": web3.eth.get_transaction_count(account_to_terminate.address),
                "gas": 200000,
                "gasPrice": web3.to_wei("20", "gwei"),
            }
        )

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt["status"] == 1:
            rental_contract.status = "terminated"
            rental_contract.save()

            ContractTermination.objects.create(
                contract=rental_contract,
                terminated_by=account_to_terminate.address,
                termination_transaction_hash=tx_hash.hex(),
            )

            ContractEvent.objects.create(
                contract=rental_contract,
                event_type="terminate",
                event_data={
                    "from_address": account_to_terminate.address,
                    "details": "Contrato encerrado.",
                },
                transaction_hash=tx_hash.hex(),
                user_address=account_to_terminate.address,
            )

            return Response(
                {
                    "message": "Contrato encerrado com sucesso!",
                    "tx_hash": tx_hash.hex(),
                },
                status=200,
            )
        else:
            return Response(
                {"error": "Falha na transação de encerramento."}, status=500
            )

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
def contract_events_api(request, contract_id):
    rental_contract = get_object_or_404(RentalContract, id=contract_id)
    events = rental_contract.events.all()
    event_data = [
        {
            "event_type": event.event_type,
            "tx_hash": event.transaction_hash,
            "from_address": event.user_address,
            "event_data": event.event_data,
            "timestamp": event.timestamp,
            "block_number": event.block_number,
            "gas_used": event.gas_used,
        }
        for event in events
    ]
    return Response(event_data)

@api_view(["POST"])
def simular_tempo(request, contract_id):
    web3 = check_connection()

    try:
        contrato = RentalContract.objects.get(id=contract_id)
        simulated_date_str = request.data.get("simulated_date")
        private_key = request.data.get("private_key")

        if not simulated_date_str:
            return Response({"error": "Data simulada não foi enviada."}, status=400)

        try:
            simulated_timestamp = datetime.datetime.strptime(
                simulated_date_str, "%Y-%m-%d"
            ).timestamp()
            simulated_date = datetime.datetime.fromtimestamp(simulated_timestamp).date()
        except ValueError:
            return Response(
                {"error": "Formato de data inválido. Use o formato 'YYYY-MM-DD'."},
                status=400,
            )

        if simulated_date < datetime.date.today():
            return Response(
                {"error": "A data simulada deve ser no futuro."}, status=400
            )

        contract_instance = web3.eth.contract(
            address=contrato.contract_address, abi=contract_abi
        )

        # Verificar se o contrato está ativo
        is_active = contract_instance.functions.isContractActive().call()
        if not is_active:
            return Response({"error": "O contrato não está ativo."}, status=400)

        # Executar a simulação de tempo
        try:
            tx_hash = contract_instance.functions.simularPassagemDeTempo(
                int(simulated_timestamp)
            ).transact(
                {
                    "from": web3.eth.account.from_key(private_key).address,
                    "gas": 3000000,
                    "gasPrice": web3.to_wei("20", "gwei"),
                }
            )

            web3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            return Response(
                {"error": f"Erro ao simular tempo no contrato: {str(e)}"}, status=400
            )

        if simulated_date >= contrato.end_date:
            contrato.end_date += relativedelta(months=contrato.contract_duration)

        contrato.simulated_time = simulated_date
        contrato.save()

        return Response(
            {
                "message": "Tempo simulado e contrato atualizado.",
                "tx_hash": tx_hash.hex(),
                "end_date": contrato.end_date,
                "simulated_time": contrato.simulated_time,
            },
            status=200,
        )

    except RentalContract.DoesNotExist:
        return Response({"error": "Contrato não encontrado."}, status=404)
    except ValueError as ve:
        return Response({"error": str(ve)}, status=400)
    except Exception as e:
        return Response({"error": f"Erro ao simular tempo: {str(e)}"}, status=400)

@csrf_exempt
def login(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            login = data.get("login")

            if not login:
                return JsonResponse({"success": False, "error": "Login é obrigatório"}, status=400)

            # Buscar o ID e o endereço da wallet
            usuario = Usuario.objects.only("id", "login", "wallet_address", "is_landlord").get(login__iexact=login)
            return JsonResponse({
                "success": True,
                "user_id": usuario.id,
                "user_login": usuario.login,
                "wallet_address": usuario.wallet_address,
                "is_landlord": usuario.is_landlord
            })
        except Usuario.DoesNotExist:
            return JsonResponse({"success": False, "error": "Usuário não encontrado"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Erro ao decodificar JSON"}, status=400)
    return JsonResponse({"error": "Método não permitido"}, status=405)

def get_landlord_address(request):
    try:
        landlord = Usuario.objects.get(is_landlord=True)
        return JsonResponse({
            "success": True,
            "wallet_address": landlord.wallet_address
        })
    except Usuario.DoesNotExist:
        return JsonResponse({"success": False, "error": "Locador não encontrado"}, status=404)
    
@api_view(["POST"])
def check_and_auto_renew(request):
    web3 = check_connection()
    contracts = RentalContract.objects.filter(status="active")

    for contract in contracts:
        try:
            smart_contract = web3.eth.contract(
                address=Web3.to_checksum_address(contract.contract_address),
                abi=contract_abi,
            )

            # Obter a data de término do contrato no blockchain
            contract_end_date = smart_contract.functions.getContractEndDate().call()

            # Verificar se o contrato precisa ser renovado
            if int(time.time()) >= contract_end_date:
                # Chamar a função de renovação automaticamente
                tx = smart_contract.functions.autoRenew().build_transaction({
                    "from": contract.landlord,
                    "nonce": web3.eth.get_transaction_count(contract.landlord),
                    "gas": 200000,
                    "gasPrice": web3.to_wei("20", "gwei"),
                })

                # Descriptografar a chave privada do locador
                landlord_user = Usuario.objects.get(wallet_address=contract.landlord)
                private_key = decrypt_key(landlord_user.private_key)

                # Assinar e enviar a transação
                signed_tx = web3.eth.account.sign_transaction(tx, private_key)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

                # Atualizar a nova data de término no modelo
                new_end_date = smart_contract.functions.getContractEndDate().call()
                contract.end_date = datetime.fromtimestamp(new_end_date)

                contract.status = "active"
                contract.save()

                # Logar evento de renovação no banco
                ContractEvent.objects.create(
                    contract=contract,
                    event_type="auto_renew",
                    event_data={"tx_hash": tx_hash.hex(), "new_end_date": new_end_date},
                    transaction_hash=tx_hash.hex(),
                    user_address=contract.landlord,
                )

        except Exception as e:
            ContractEvent.objects.create(
                contract=contract,
                event_type="error",
                event_data={"details": str(e)},
            )
            continue

    return Response({"message": "Verificação e renovação automáticas concluídas."}, status=200)

@api_view(["GET"])
def get_pending_contracts(request):
    """
    Retorna contratos pendentes filtrados pelo usuário logado.
    """
    try:
        user_address = request.query_params.get("user_address")
        user_type = request.query_params.get("user_type")

        if not user_address or not user_type:
            return Response(
                {"error": "Parâmetros 'user_address' e 'user_type' são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_type == "landlord":
            contracts = RentalContract.objects.filter(
                landlord=user_address, status="pending"
            )
        elif user_type == "tenant":
            contracts = RentalContract.objects.filter(
                tenant=user_address, status="pending"
            )
        else:
            return Response(
                {"error": "Tipo de usuário inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RentalContractSerializer(contracts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def fetch_users(request):
    """
    Retorna uma lista de todos os usuários com seus endereços de carteira, ids e nomes.
    """
    try:
        # Exemplo: Pegando os campos que você quer retornar (ID, username e email)
        users = User.objects.all().values("login", "wallet_address")
        return Response(users, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
