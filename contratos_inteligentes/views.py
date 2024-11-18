from datetime import datetime
import json
import os
import traceback
from decimal import Decimal
import time

from dateutil.relativedelta import relativedelta  # type:ignore
from django.views.decorators.csrf import csrf_exempt # type: ignore
from django.http import JsonResponse  # type:ignore
from django.shortcuts import get_object_or_404  # type:ignore
from django.utils import timezone  # type:ignore
from dotenv import load_dotenv  # type:ignore
from rest_framework import status  # type:ignore
from rest_framework.decorators import api_view  # type:ignore
from rest_framework.response import Response  # type:ignore
from web3 import Account, Web3  # type:ignore

from .models import ContractEvent, ContractTermination, Payment, RentalContract, Usuario
from .utils.check_connection import check_connection
from .utils.load_contract_data import load_contract_data
from .utils.log_contract_event import log_contract_event
from .utils.normalize_address import normalize_address

contract_abi, bytecode = load_contract_data()

# global_contract_address = Web3.to_checksum_address("0x5fbdb2315678afecb367f032d93f642f64180aa3")
# global_contract = web3.eth.contract(address=global_contract_address, abi=contract_abi)

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
        
        start_date = datetime.strptime(request.data["start_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=None)
        end_date = datetime.strptime(request.data["end_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=None)

        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        private_key = request.data["private_key"]

        if end_timestamp <= start_timestamp:
            return Response(
                {"error": "A data de término deve ser posterior à data de início."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contract_duration = end_timestamp - start_timestamp
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
            start_timestamp,
            end_timestamp,
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
            start_date=datetime.fromtimestamp(start_timestamp),
            end_date=datetime.fromtimestamp(end_timestamp),
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

    try:
        web3 = check_connection()
    except Exception as e:
        return JsonResponse(
            {"error": "Falha ao conectar ao Web3: " + str(e)}, status=500
        )

    try:
        account_to_sign = web3.eth.account.from_key(private_key)
    except ValueError:
        return JsonResponse({"error": "Chave privada inválida."}, status=400)

    try:
        landlord = normalize_address(rental_contract.landlord)
        tenant = normalize_address(rental_contract.tenant)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    try:
        smart_contract = web3.eth.contract(
            address=Web3.to_checksum_address(rental_contract.contract_address),
            abi=contract_abi,
        )
    except Exception as e:
        return JsonResponse({"error": f"Erro ao carregar o contrato: {str(e)}"}, status=500)

    if not smart_contract.functions.isContractActive().call():
        return JsonResponse(
            {"error": "O contrato já foi encerrado e não pode ser assinado."},
            status=403,
        )

    if smart_contract.functions.isFullySigned().call():
        return JsonResponse(
            {"error": "O contrato já foi assinado por ambas as partes."}, status=403
        )

    if user_type == "landlord" and account_to_sign.address.lower() != landlord.lower():
        return JsonResponse(
            {"error": "Apenas o locador pode assinar como 'landlord'."}, status=403
        )
    if user_type == "tenant" and account_to_sign.address.lower() != tenant.lower():
        return JsonResponse(
            {"error": "Apenas o inquilino pode assinar como 'tenant'."}, status=403
        )

    nonce = web3.eth.get_transaction_count(account_to_sign.address)

    try:
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

        if tx_receipt["status"] == 1:
            if user_type == "landlord":
                rental_contract.landlord_signature = account_to_sign.address
            elif user_type == "tenant":
                rental_contract.tenant_signature = account_to_sign.address

            if rental_contract.is_fully_signed():
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
        else:
            return JsonResponse(
                {"error": "Falha na transação de assinatura."}, status=500
            )

    except Exception as e:
        return JsonResponse(
            {"error": f"Erro ao assinar o contrato: {str(e)}"}, status=500
        )

@api_view(["POST"])
def register_payment_api(request, contract_id):
    try:
        web3 = check_connection()
        rental_contract = get_object_or_404(RentalContract, id=contract_id)
        private_key = request.data.get("private_key")
        payment_type = request.data.get("payment_type")  # 'Aluguel' ou 'Depósito'
        amount = request.data.get("amount")

        if not amount or int(amount) <= 0:
            return Response({"error": "Valor do pagamento inválido."}, status=400)

        try:
            account_to_pay = web3.eth.account.from_key(private_key)
        except ValueError:
            return Response({"error": "Chave privada inválida."}, status=400)

        # Verificar se o endereço é o locador ou o inquilino
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

        # Carregar o contrato inteligente
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

        # Verifica se o valor do pagamento corresponde ao esperado
        if payment_type == "Aluguel":
            tx_function = smart_contract.functions.payRent()
            expected_amount = smart_contract.functions.getRentAmount().call()
        elif payment_type == "Depósito":
            tx_function = smart_contract.functions.payDeposit()
            expected_amount = smart_contract.functions.getDepositAmount().call()
        else:
            return Response({"error": "Tipo de pagamento inválido."}, status=400)

        # Verificar se o valor está correto
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
                    "value": int(amount),  # Enviar o valor já em Wei
                    "nonce": web3.eth.get_transaction_count(account_to_pay.address),
                    "gas": 200000,
                    "gasPrice": web3.to_wei("20", "gwei"),
                }
            )

            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            # Esperar pelo recibo da transação
            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            if tx_receipt["status"] == 1:
                # Registrar o pagamento no banco de dados
                Payment.objects.create(
                    contract=rental_contract,
                    amount=amount,  # Valor em Wei
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
    contracts = RentalContract.objects.all()
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
    return Response(contracts_data)


@api_view(["POST"])
def terminate_contract_api(request, contract_id):
    rental_contract = get_object_or_404(RentalContract, id=contract_id)
    private_key = request.data.get("private_key")

    web3 = check_connection()

    try:
        account_to_terminate = web3.eth.account.from_key(private_key)
    except ValueError:
        return Response({"error": "Chave privada inválida."}, status=400)

    # Verificar se o endereço é o locador ou o inquilino
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
            # Atualizar o status do contrato no banco de dados
            rental_contract.status = "terminated"
            rental_contract.save()

            # Registrar o evento de encerramento
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