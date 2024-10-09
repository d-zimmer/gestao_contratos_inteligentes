from django.shortcuts import get_object_or_404 # type:ignore
from rest_framework.decorators import api_view # type:ignore
from rest_framework.response import Response # type:ignore
from web3 import Web3, Account # type:ignore
from .models import RentalContract, Payment, ContractTermination, ContractEvent
from django.utils import timezone # type:ignore
from dotenv import load_dotenv # type:ignore
import os
import json
import traceback
import datetime
from decimal import Decimal

load_dotenv()

# Conectar ao Ganache
web3 = Web3(Web3.HTTPProvider(os.getenv("GANACHE_URL")))

# Função para carregar os dados do contrato (ABI e Bytecode)
def load_contract_data():
    with open(os.path.join('build', 'RentalAgreementABI.json'), 'r') as abi_file:
        contract_abi = json.load(abi_file)
    with open(os.path.join('build', 'compiled_contract.json'), 'r') as bytecode_file:
        compiled_contract = json.load(bytecode_file)
        bytecode = compiled_contract["contracts"]["RentalAgreement.sol"]["RentalAgreement"]["evm"]["bytecode"]["object"]
    return contract_abi, bytecode

# Função para verificar a conexão com o Ganache
def check_connection():
    if not web3.is_connected():
        raise Exception("Não conectado à rede Ethereum. Verifique sua conexão.")

# Verificar a conexão com o Ganache
if web3.is_connected():
    print("Conectado à rede local Ganache")
else:
    print("Erro ao conectar")

# Carregar ABI e Bytecode uma vez
contract_abi, bytecode = load_contract_data()

# Função para normalizar e verificar o endereço
def normalize_address(address):
    try:
        return Web3.to_checksum_address(address)
    except ValueError:
        raise ValueError(f"Endereço inválido: {address}")

# Definir o endereço do contrato global
global_contract_address = Web3.to_checksum_address("0x5fbdb2315678afecb367f032d93f642f64180aa3")
global_contract = web3.eth.contract(address=global_contract_address, abi=contract_abi)

def log_contract_event(contract, event_type, user_address, tx_hash=None, event_data=None):
    ContractEvent.objects.create(
        contract=contract,
        event_type=event_type,
        user_address=user_address,
        event_data=event_data or {},
        transaction_hash=tx_hash
    )

@api_view(['GET'])
def contract_list_api(request):
    contracts = RentalContract.objects.all()
    contracts_data = [{
        "id": contract.id,
        "landlord": contract.landlord,
        "tenant": contract.tenant,
        "rent_amount": str(contract.rent_amount),
        "deposit_amount": str(contract.deposit_amount),
        "contract_address": contract.contract_address,
        "status": contract.status,
        "created_at": contract.created_at
    } for contract in contracts]
    return Response(contracts_data)

@api_view(['POST'])
def create_contract_api(request):
    try:
        check_connection()  # Verificar a conexão com o Ganache
    except Exception as e:
        return Response({"error": "Falha na conexão com a rede Ethereum: " + str(e)}, status=500)

    landlord = request.data.get('landlord')
    tenant = request.data.get('tenant')
    rent_amount = request.data.get('rent_amount')
    deposit_amount = request.data.get('deposit_amount')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')
    contract_duration = request.data.get('contract_duration')
    private_key = request.data.get('private_key')

    if not rent_amount or not deposit_amount or not contract_duration:
        return Response({"error": "Valores de aluguel, depósito ou duração do contrato inválidos"}, status=400)

    try:
        rent_amount = int(rent_amount)  # Já é passado em Wei
        deposit_amount = int(deposit_amount)  # Já é passado em Wei
        contract_duration = int(contract_duration)
    except ValueError:
        return Response({"error": "Valores de aluguel, depósito ou duração do contrato devem ser números válidos."}, status=400)

    try:
        account = web3.eth.account.from_key(private_key)
    except ValueError:
        return Response({"error": "Chave privada inválida."}, status=400)

    try:
        landlord = normalize_address(landlord)
        tenant = normalize_address(tenant)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    smart_contract = web3.eth.contract(abi=contract_abi, bytecode=bytecode)

    try:
        transaction = smart_contract.constructor(tenant, rent_amount, deposit_amount).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': 3000000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        new_contract_address = tx_receipt.contractAddress

        RentalContract.objects.create(
            landlord=landlord,
            tenant=tenant,
            rent_amount=rent_amount,
            deposit_amount=deposit_amount,
            contract_address=new_contract_address,
            status='pending',
            start_date=start_date,
            end_date=end_date,
            contract_duration=contract_duration,
        )

        return Response({
            "message": "Contrato criado com sucesso!",
            "tx_hash": tx_hash.hex(),
            "contract_address": new_contract_address
        }, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def recurring_payment_api(request, contract_id):
    try:
        check_connection()
        rental_contract = get_object_or_404(RentalContract, id=contract_id)
        private_key = request.data.get('private_key')
        payment_type = request.data.get('payment_type')  # 'Aluguel' ou 'Depósito'
        amount = request.data.get('amount')

        if not amount or float(amount) <= 0:
            return Response({"error": "Valor do pagamento inválido."}, status=400)

        account_to_pay = web3.eth.account.from_key(private_key)

        # Verificar se o contrato expirou
        if rental_contract.end_date < timezone.now():
            return Response({"error": "O contrato expirou."}, status=400)

        # Função de pagamento automatizada para evitar atrasos
        try:
            tx = global_contract.functions.payRent().build_transaction({
                'from': account_to_pay.address,
                'value': web3.to_wei(amount, 'ether'),
                'nonce': web3.eth.get_transaction_count(account_to_pay.address),
                'gas': 200000,
                'gasPrice': web3.to_wei('20', 'gwei')
            })

            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            log_contract_event(rental_contract, 'pay_rent', account_to_pay.address, tx_hash.hex())

            return Response({"message": "Pagamento registrado com sucesso!", "tx_hash": tx_hash.hex()})
        except Exception as e:
            return Response({"error": f"Erro ao registrar pagamento: {str(e)}"}, status=500)

    except Exception as e:
        return Response({"error": f"Erro ao processar pagamento: {str(e)}", "traceback": traceback.format_exc()}, status=500)

@api_view(['POST'])
def sign_contract_api(request, contract_id):
    rental_contract = get_object_or_404(RentalContract, id=contract_id)
    private_key = request.data.get('private_key')
    user_type = request.data.get('user_type')  # 'landlord' ou 'tenant'

    try:
        account_to_sign = web3.eth.account.from_key(private_key)
    except ValueError:
        return Response({"error": "Chave privada inválida."}, status=400)

    # Verificar endereços com checksum
    try:
        landlord = normalize_address(rental_contract.landlord)
        tenant = normalize_address(rental_contract.tenant)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    # Verificar o estado do contrato no blockchain antes de assinar
    smart_contract = web3.eth.contract(address=Web3.to_checksum_address(rental_contract.contract_address), abi=contract_abi)
    
    # Verificar se o contrato está ativo (não encerrado)
    is_active = smart_contract.functions.isContractActive().call()
    
    if not is_active:
        return Response({"error": "O contrato já foi encerrado e não pode mais ser assinado."}, status=403)

    # Verificar se o contrato já foi totalmente assinado
    fully_signed = smart_contract.functions.isFullySigned().call()
    
    if fully_signed:
        return Response({"error": "O contrato já foi assinado por ambas as partes."}, status=403)

    # Verificar quem está tentando assinar o contrato
    if user_type == 'landlord' and account_to_sign.address.lower() != landlord.lower():
        return Response({"error": "Somente o locador pode assinar como 'landlord'."}, status=403)

    if user_type == 'tenant' and account_to_sign.address.lower() != tenant.lower():
        return Response({"error": "Somente o inquilino pode assinar como 'tenant'."}, status=403)

    # Verificar o nonce da transação
    nonce = web3.eth.get_transaction_count(account_to_sign.address)

    try:
        # Construir e assinar a transação
        tx = smart_contract.functions.signAgreement().build_transaction({
            'from': account_to_sign.address,
            'nonce': nonce,
            'gas': 200000,  # Aumentar o limite de gás
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        # Verificar se a transação foi bem-sucedida
        if tx_receipt['status'] == 1:
            # Atualizar as assinaturas no banco de dados
            if user_type == 'landlord':
                rental_contract.landlord_signature = account_to_sign.address
            elif user_type == 'tenant':
                rental_contract.tenant_signature = account_to_sign.address

            # Verificar se ambas as assinaturas foram feitas
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

            return Response({"message": "Contrato assinado com sucesso!", "tx_hash": tx_hash.hex(), "status": rental_contract.status}, status=200)
        else:
            return Response({"error": "Falha na transação de assinatura."}, status=500)

    except Exception as e:
        return Response({"error": f"Erro ao assinar o contrato: {str(e)}"}, status=500)

@api_view(['POST'])
def register_payment_api(request, contract_id):
    try:
        check_connection()
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
            print(f"Estado atual do contrato: {contract_state}")
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

        print(f"Valor enviado: {amount_in_wei}")
        print(f"Valor esperado ({payment_type.lower()}): {expected_amount} Wei")

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

@api_view(['POST'])
def terminate_contract_api(request, contract_id):
    rental_contract = get_object_or_404(RentalContract, id=contract_id)
    private_key = request.data.get('private_key')

    try:
        account_to_terminate = web3.eth.account.from_key(private_key)
    except ValueError:
        return Response({"error": "Chave privada inválida."}, status=400)

    # Verificar se o endereço é o locador ou o inquilino
    if account_to_terminate.address.lower() != rental_contract.landlord.lower() and account_to_terminate.address.lower() != rental_contract.tenant.lower():
        return Response({"error": "Somente o locador ou o inquilino podem encerrar o contrato."}, status=403)

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

@api_view(['GET'])
def test_contract_functions(request, contract_id):
    try:
        check_connection()
        rental_contract = get_object_or_404(RentalContract, id=contract_id)
        smart_contract = web3.eth.contract(address=Web3.to_checksum_address(rental_contract.contract_address), abi=contract_abi)

        try:
            print("Chamando getRentAmount")
            rent_amount = smart_contract.functions.getRentAmount().call()
            print(f"Valor esperado do aluguel: {rent_amount} Wei")

            print("Chamando getDepositAmount")
            deposit_amount = smart_contract.functions.getDepositAmount().call()
            print(f"Valor esperado do depósito: {deposit_amount} Wei")

            return Response({
                "rent_amount": rent_amount,
                "deposit_amount": deposit_amount
            }, status=200)

        except Exception as e:
            print(f"Erro ao chamar funções do contrato: {str(e)}")
            return Response({"error": str(e)}, status=500)

    except Exception as e:
        return Response({"error": f"Erro ao processar pagamento: {str(e)}", "traceback": traceback.format_exc()}, status=500)

def registrar_evento_fallback(evento, dados, motivo_falha):
    # Registrar tentativa de evento que falhou
    ContractEvent.objects.create(
        event_type=evento,
        event_data=dados,
        status="failed",
        failure_reason=motivo_falha,
        timestamp=timezone.now()
    )

    try:
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    except Exception as e:
        registrar_evento_fallback("Pagamento", {"contrato": contract_id}, str(e))
