from django.shortcuts import get_object_or_404 # type:ignore
from rest_framework.decorators import api_view # type:ignore
from rest_framework.response import Response # type:ignore
from rest_framework import status # type:ignore
from web3 import Web3, Account # type:ignore
from .models import RentalContract, Payment, ContractTermination, ContractEvent
from django.utils import timezone # type:ignore
from django.http import JsonResponse # type:ignore
from dotenv import load_dotenv # type:ignore
import os
import json
import traceback
import datetime
from dateutil.relativedelta import relativedelta # type:ignore
from decimal import Decimal
from .utils.load_contract_data import load_contract_data
from .utils.check_connection import check_connection
from .utils.normalize_address import normalize_address
from .utils.log_contract_event import log_contract_event

contract_abi, bytecode = load_contract_data()

# global_contract_address = Web3.to_checksum_address("0x5fbdb2315678afecb367f032d93f642f64180aa3")
# global_contract = web3.eth.contract(address=global_contract_address, abi=contract_abi)

@api_view(['POST'])
def create_contract_api(request):
    try:
        web3 = check_connection()
    except Exception as e:
        return Response({"error": "Falha na conexão com a rede Ethereum: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    required_fields = ['landlord', 'tenant', 'rent_amount', 'deposit_amount', 'start_date', 'end_date', 'contract_duration', 'private_key']
    for field in required_fields:
        if not request.data.get(field):
            return Response({"error": f"O campo '{field}' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

    landlord = request.data['landlord']
    tenant = request.data['tenant']
    rent_amount = request.data['rent_amount']
    deposit_amount = request.data['deposit_amount']
    start_date = request.data['start_date']
    end_date = request.data['end_date']
    contract_duration = request.data['contract_duration']
    private_key = request.data['private_key']

    try:
        rent_amount = int(rent_amount)
        deposit_amount = int(deposit_amount)
        contract_duration = int(contract_duration)
        if rent_amount <= 0 or deposit_amount <= 0 or contract_duration <= 0:
            raise ValueError("Valores devem ser maiores que zero.")
    except ValueError:
        return Response({"error": "Valores de aluguel, depósito ou duração do contrato devem ser números válidos e maiores que zero."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        account = web3.eth.account.from_key(private_key)
    except ValueError:
        return Response({"error": "Chave privada inválida."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        landlord = normalize_address(landlord)
        tenant = normalize_address(tenant)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        if end_date <= start_date:
            return Response({"error": "A data de término deve ser posterior à data de início."}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({"error": "Formato de data inválido. Use 'YYYY-MM-DD'."}, status=status.HTTP_400_BAD_REQUEST)

    smart_contract = web3.eth.contract(abi=contract_abi, bytecode=bytecode)
    try:
        transaction = smart_contract.constructor(tenant, rent_amount, deposit_amount, contract_duration).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': 3000000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        new_contract_address = tx_receipt.contractAddress
        rent_due_date = start_date + relativedelta(months=1)

        new_contract = RentalContract.objects.create(
            landlord=landlord,
            tenant=tenant,
            rent_amount=rent_amount,
            deposit_amount=deposit_amount,
            contract_address=new_contract_address,
            status='pending',
            start_date=start_date,
            end_date=end_date,
            rent_due_date=rent_due_date,
            contract_duration=contract_duration,
        )

        # Responder com sucesso
        return Response({
            "message": "Contrato criado com sucesso!",
            "tx_hash": tx_hash.hex(),
            "contract_address": new_contract_address,
            "start_date": start_date,
            "end_date": end_date,
            "rent_due_date": rent_due_date,
            "id": new_contract.id  # Retorna o ID do contrato criado no banco de dados
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def sign_contract_api(request, contract_id):
    # Recuperar o contrato do banco de dados
    rental_contract = RentalContract.objects.filter(id=contract_id).first()
    if not rental_contract:
        return JsonResponse({"error": "Contrato não encontrado."}, status=404)

    private_key = request.data.get('private_key')
    user_type = request.data.get('user_type')  # 'landlord' ou 'tenant'

    # Verificar se os dados necessários foram fornecidos
    if not private_key or not user_type:
        return JsonResponse({"error": "Chave privada e tipo de usuário são obrigatórios."}, status=400)

    # Conectar ao Web3
    web3 = check_connection()

    # Verificar a validade da chave privada
    try:
        account_to_sign = web3.eth.account.from_key(private_key)
    except ValueError:
        return JsonResponse({"error": "Chave privada inválida."}, status=400)

    # Normalizar e verificar os endereços do locador e inquilino
    try:
        landlord = normalize_address(rental_contract.landlord)
        tenant = normalize_address(rental_contract.tenant)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    # Verificar o estado do contrato no blockchain
    smart_contract = web3.eth.contract(
        address=Web3.to_checksum_address(rental_contract.contract_address),
        abi=contract_abi
    )
    
    # Verificar se o contrato está ativo e não foi encerrado
    if not smart_contract.functions.isContractActive().call():
        return JsonResponse({"error": "O contrato já foi encerrado e não pode ser assinado."}, status=403)

    # Verificar se o contrato já está totalmente assinado
    if smart_contract.functions.isFullySigned().call():
        return JsonResponse({"error": "O contrato já foi assinado por ambas as partes."}, status=403)

    # Validar o usuário que está tentando assinar
    if user_type == 'landlord' and account_to_sign.address.lower() != landlord.lower():
        return JsonResponse({"error": "Apenas o locador pode assinar como 'landlord'."}, status=403)
    if user_type == 'tenant' and account_to_sign.address.lower() != tenant.lower():
        return JsonResponse({"error": "Apenas o inquilino pode assinar como 'tenant'."}, status=403)

    # Recuperar o nonce da transação
    nonce = web3.eth.get_transaction_count(account_to_sign.address)

    try:
        # Construir e assinar a transação
        transaction = smart_contract.functions.signAgreement().build_transaction({
            'from': account_to_sign.address,
            'nonce': nonce,
            'gas': 300000,  # Aumentar o limite de gás para maior segurança
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        # Assinar e enviar a transação
        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        # Verificar o resultado da transação
        if tx_receipt['status'] == 1:
            # Atualizar as assinaturas no banco de dados
            if user_type == 'landlord':
                rental_contract.landlord_signature = account_to_sign.address
            elif user_type == 'tenant':
                rental_contract.tenant_signature = account_to_sign.address

            # Verificar se o contrato foi totalmente assinado
            if rental_contract.is_fully_signed():
                rental_contract.status = 'active'

            rental_contract.save()

            # Registrar o evento de assinatura
            ContractEvent.objects.create(
                contract=rental_contract,
                event_type='sign',
                user_address=account_to_sign.address,
                event_data={
                    'tx_hash': tx_hash.hex(),
                    'user_type': user_type
                },
                transaction_hash=tx_hash.hex()
            )

            return JsonResponse({
                "message": "Contrato assinado com sucesso!",
                "tx_hash": tx_hash.hex(),
                "status": rental_contract.status
            }, status=200)
        else:
            return JsonResponse({"error": "Falha na transação de assinatura."}, status=500)

    except Exception as e:
        return JsonResponse({"error": f"Erro ao assinar o contrato: {str(e)}"}, status=500)

@api_view(['POST'])
def register_payment_api(request, contract_id):
    try:
        web3 = check_connection()
        rental_contract = get_object_or_404(RentalContract, id=contract_id)
        private_key = request.data.get('private_key')
        payment_type = request.data.get('payment_type')  # 'Aluguel' ou 'Depósito'
        amount = request.data.get('amount')

        if not amount or float(amount) <= 0:
            return Response({"error": "Valor do pagamento inválido."}, status=400)

        try:
            account_to_pay = web3.eth.account.from_key(private_key)
        except ValueError:
            return Response({"error": "Chave privada inválida."}, status=400)

        # Verificar se o endereço é o locador ou o inquilino
        if account_to_pay.address.lower() != rental_contract.landlord.lower() and account_to_pay.address.lower() != rental_contract.tenant.lower():
            return Response({"error": "Somente o locador ou o inquilino podem registrar pagamentos."}, status=403)

        # Carregar o contrato inteligente
        smart_contract = web3.eth.contract(address=Web3.to_checksum_address(rental_contract.contract_address), abi=contract_abi)
        
        # Chamar a função para verificar o estado do contrato
        try:
            contract_state = smart_contract.functions.getContractState().call()
            # print(f"Estado atual do contrato: {contract_state}")
        except Exception as e:
            print(f"Erro ao obter estado do contrato: {str(e)}")
            return Response({"error": f"Erro ao obter estado do contrato: {str(e)}"}, status=500)

        # Continuar com o fluxo de pagamento após verificar o estado
        if payment_type == "Aluguel":
            tx_function = smart_contract.functions.payRent()
            expected_amount = smart_contract.functions.getRentAmount().call()
        elif payment_type == "Depósito":
            tx_function = smart_contract.functions.payDeposit()
            expected_amount = smart_contract.functions.getDepositAmount().call()
        else:
            return Response({"error": "Tipo de pagamento inválido."}, status=400)

        # Converter o valor do pagamento para Wei
        amount_in_wei = web3.to_wei(amount, 'ether')

        # print(f"Valor enviado: {amount_in_wei}")
        # print(f"Valor esperado ({payment_type.lower()}): {expected_amount} Wei")

        # Verificar o valor esperado diretamente no contrato
        if amount_in_wei != expected_amount:
            return Response({
                "error": f"Valor incorreto para {payment_type}. Esperado: {expected_amount} Wei, Recebido: {amount_in_wei} Wei"
            }, status=400)

        try:
            tx = tx_function.build_transaction({
                'from': account_to_pay.address,
                'value': amount_in_wei,  # Enviar o valor convertido para Wei
                'nonce': web3.eth.get_transaction_count(account_to_pay.address),
                'gas': 200000,
                'gasPrice': web3.to_wei('20', 'gwei')
            })

            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            # Esperar pelo recibo da transação
            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            if tx_receipt['status'] == 1:
                # Registrar o pagamento no banco de dados
                Payment.objects.create(
                    contract=rental_contract,
                    amount=amount,  # Valor original
                    payment_type='rent' if payment_type == "Aluguel" else 'deposit',
                    transaction_hash=tx_hash.hex(),
                    is_verified=True
                )

                # Registrar o evento de pagamento
                ContractEvent.objects.create(
                    contract=rental_contract,
                    event_type='pay_rent' if payment_type == "Aluguel" else 'pay_deposit',
                    event_data={
                        'tx_hash': tx_hash.hex(),
                        'from_address': account_to_pay.address,
                        'amount': amount
                    },
                    transaction_hash=tx_hash.hex(),
                    user_address=account_to_pay.address
                )

                return Response({"message": f"Pagamento de {payment_type} registrado com sucesso!", "tx_hash": tx_hash.hex()}, status=200)
            else:
                return Response({"error": "Falha na transação de pagamento."}, status=500)

        except Exception as e:
            return Response({"error": f"Erro ao registrar pagamento: {str(e)}"}, status=500)

    except Exception as e:
        return Response({"error": f"Erro ao processar pagamento: {str(e)}", "traceback": traceback.format_exc()}, status=500)
    
@api_view(['GET'])
def contract_list_api(request):
    contracts = RentalContract.objects.all()
    contracts_data = [{
        "id": contract.id,
        "landlord": contract.landlord,
        "tenant": contract.tenant,
        "rent_amount": str(contract.rent_amount),
        "deposit_amount": str(contract.deposit_amount),
        'start_date': str(contract.start_date),
        'end_date': str(contract.end_date),
        "contract_address": contract.contract_address,
        "status": contract.status,
        "created_at": contract.created_at
    } for contract in contracts]
    return Response(contracts_data)

@api_view(['POST'])
def terminate_contract_api(request, contract_id):
    rental_contract = get_object_or_404(RentalContract, id=contract_id)
    private_key = request.data.get('private_key')

    web3 = check_connection()

    try:
        account_to_terminate = web3.eth.account.from_key(private_key)
    except ValueError:
        return Response({"error": "Chave privada inválida."}, status=400)

    # Verificar se o endereço é o locador ou o inquilino
    if account_to_terminate.address.lower() != rental_contract.landlord.lower() and account_to_terminate.address.lower() != rental_contract.tenant.lower():
        return Response({"error": "Somente o locador ou o inquilino podem encerrar o contrato."}, status=403)

    if not rental_contract.is_fully_signed():
        return Response({"error": "O contrato precisa ser assinado por ambas as partes antes de ser encerrado."}, status=400)

    smart_contract = web3.eth.contract(address=Web3.to_checksum_address(rental_contract.contract_address), abi=contract_abi)

    try:
        tx = smart_contract.functions.terminateContract().build_transaction({
            'from': account_to_terminate.address,
            'nonce': web3.eth.get_transaction_count(account_to_terminate.address),
            'gas': 200000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt['status'] == 1:
            # Atualizar o status do contrato no banco de dados
            rental_contract.status = 'terminated'
            rental_contract.save()

            # Registrar o evento de encerramento
            ContractTermination.objects.create(
                contract=rental_contract,
                terminated_by=account_to_terminate.address,
                termination_transaction_hash=tx_hash.hex()
            )

            ContractEvent.objects.create(
                contract=rental_contract,
                event_type='terminate',
                event_data={
                    'from_address': account_to_terminate.address,
                    'details': 'Contrato encerrado.'
                },
                transaction_hash=tx_hash.hex(),  
                user_address=account_to_terminate.address
            )

            return Response({"message": "Contrato encerrado com sucesso!", "tx_hash": tx_hash.hex()}, status=200)
        else:
            return Response({"error": "Falha na transação de encerramento."}, status=500)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def contract_events_api(request, contract_id):
    rental_contract = get_object_or_404(RentalContract, id=contract_id)
    events = rental_contract.events.all()
    event_data = [{
        "event_type": event.event_type,
        "tx_hash": event.transaction_hash,
        "from_address": event.user_address,
        "event_data": event.event_data,
        "timestamp": event.timestamp,
        "block_number": event.block_number,
        "gas_used": event.gas_used
    } for event in events]
    return Response(event_data)

@api_view(['POST'])
def simular_tempo(request, contract_id):
    web3 = check_connection()

    try:
        contrato = RentalContract.objects.get(id=contract_id)
        simulated_date_str = request.data.get('simulated_date')
        private_key = request.data.get('private_key')

        if not simulated_date_str:
            return Response({"error": "Data simulada não foi enviada."}, status=400)

        try:
            simulated_timestamp = datetime.datetime.strptime(simulated_date_str, '%Y-%m-%d').timestamp()
            simulated_date = datetime.datetime.fromtimestamp(simulated_timestamp).date()
        except ValueError:
            return Response({"error": "Formato de data inválido. Use o formato 'YYYY-MM-DD'."}, status=400)

        if simulated_date < datetime.date.today():
            return Response({"error": "A data simulada deve ser no futuro."}, status=400)

        contract_instance = web3.eth.contract(address=contrato.contract_address, abi=contract_abi)

        # Verificar se o contrato está ativo
        is_active = contract_instance.functions.isContractActive().call()
        if not is_active:
            return Response({"error": "O contrato não está ativo."}, status=400)

        # Executar a simulação de tempo
        try:
            tx_hash = contract_instance.functions.simularPassagemDeTempo(int(simulated_timestamp)).transact({
                'from': web3.eth.account.from_key(private_key).address,
                'gas': 3000000,
                'gasPrice': web3.to_wei('20', 'gwei')
            })

            web3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            return Response({"error": f"Erro ao simular tempo no contrato: {str(e)}"}, status=400)

        if simulated_date >= contrato.end_date:
            contrato.end_date += relativedelta(months=contrato.contract_duration)

        contrato.simulated_time = simulated_date
        contrato.save()

        return Response({
            'message': 'Tempo simulado e contrato atualizado.',
            'tx_hash': tx_hash.hex(),
            'end_date': contrato.end_date,
            'simulated_time': contrato.simulated_time
        }, status=200)

    except RentalContract.DoesNotExist:
        return Response({"error": "Contrato não encontrado."}, status=404)
    except ValueError as ve:
        return Response({"error": str(ve)}, status=400)
    except Exception as e:
        return Response({"error": f"Erro ao simular tempo: {str(e)}"}, status=400)
