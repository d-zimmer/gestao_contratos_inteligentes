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
        check_connection()
    except Exception as e:
        return Response({"error": "Falha na conexão com a rede Ethereum: " + str(e)}, status=500)

    landlord = request.data.get('landlord')
    tenant = request.data.get('tenant')
    rent_amount = request.data.get('rent_amount')
    deposit_amount = request.data.get('deposit_amount')
    private_key = request.data.get('private_key')

    if not rent_amount or not deposit_amount:
        return Response({"error": "Valores de aluguel ou depósito inválidos"}, status=400)

    try:
        rent_amount = int(rent_amount)
        deposit_amount = int(deposit_amount)
    except ValueError:
        return Response({"error": "Valores de aluguel ou depósito devem ser números inteiros válidos."}, status=400)

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
            status='pending'
        )

        return Response({
            "message": "Contrato criado com sucesso!",
            "tx_hash": tx_hash.hex(),
            "contract_address": new_contract_address
        }, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def pay_rent_api(request, contract_id):
    try:
        check_connection()
        
        rental_contract = get_object_or_404(RentalContract, id=contract_id)
        tenant_address = request.data.get('tenant_address')
        rent_amount = request.data.get('rent_amount')
        private_key = request.data.get('private_key')

        if not rent_amount or float(rent_amount) <= 0:
            return Response({"error": "Valor do aluguel inválido."}, status=400)

        if not Web3.is_address(tenant_address):
            return Response({"error": "Endereço do inquilino inválido."}, status=400)
        
        tenant_address = Web3.to_checksum_address(tenant_address)

        try:
            account_to_pay = web3.eth.account.from_key(private_key)
        except ValueError:
            return Response({"error": "Chave privada inválida."}, status=400)

        # Verificar se o endereço que está pagando é o inquilino
        if account_to_pay.address.lower() != rental_contract.tenant.lower():
            return Response({"error": "Somente o inquilino pode pagar o aluguel."}, status=403)

        smart_contract = web3.eth.contract(address=Web3.to_checksum_address(rental_contract.contract_address), abi=contract_abi)

        try:
            tx = smart_contract.functions.payRent().build_transaction({
                'from': account_to_pay.address,
                'value': web3.to_wei(rent_amount, 'ether'),
                'nonce': web3.eth.get_transaction_count(account_to_pay.address),
                'gas': 200000,
                'gasPrice': web3.to_wei('20', 'gwei')
            })

            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            # Verificar se a transação foi bem-sucedida
            if tx_receipt['status'] == 1:
                # Registrar o pagamento no banco de dados
                Payment.objects.create(
                    contract=rental_contract,
                    amount=rent_amount,
                    payment_type='rent',
                    transaction_hash=tx_hash.hex(),
                    is_verified=True
                )

                # Registrar o evento de pagamento
                ContractEvent.objects.create(
                    contract=rental_contract,
                    event_type='pay_rent',
                    event_data={
                        'tx_hash': tx_hash.hex(),
                        'from_address': account_to_pay.address,
                        'amount': rent_amount
                    },
                    tx_hash=tx_hash.hex(),
                    user_address=account_to_pay.address
                )

                return Response({"message": "Aluguel pago com sucesso!", "tx_hash": tx_hash.hex()})
            else:
                return Response({"error": "Falha na transação de pagamento."}, status=500)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

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

    print(f"Endereço derivado da chave privada: {account_to_sign.address}")
    print(f"Endereço do locador no contrato: {landlord}")
    print(f"Endereço do inquilino no contrato: {tenant}")

    # Verificar o estado do contrato no blockchain antes de assinar
    smart_contract = web3.eth.contract(address=Web3.to_checksum_address(rental_contract.contract_address), abi=contract_abi)
    
    # Verificar se o contrato está ativo (não encerrado)
    is_active = smart_contract.functions.isContractActive().call()
    print(f"Contrato ativo: {is_active}")
    
    if not is_active:
        return Response({"error": "O contrato já foi encerrado e não pode mais ser assinado."}, status=403)

    # Verificar se o contrato já foi totalmente assinado
    fully_signed = smart_contract.functions.isFullySigned().call()
    print(f"Contrato já assinado completamente: {fully_signed}")
    
    if fully_signed:
        return Response({"error": "O contrato já foi assinado por ambas as partes."}, status=403)

    # Verificar quem está tentando assinar o contrato
    if user_type == 'landlord' and account_to_sign.address.lower() != landlord.lower():
        return Response({"error": "Somente o locador pode assinar como 'landlord'."}, status=403)

    if user_type == 'tenant' and account_to_sign.address.lower() != tenant.lower():
        return Response({"error": "Somente o inquilino pode assinar como 'tenant'."}, status=403)

    # Verificar o nonce da transação
    nonce = web3.eth.get_transaction_count(account_to_sign.address)
    print(f"Nonce atual para o endereço {account_to_sign.address}: {nonce}")

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
        error_traceback = traceback.format_exc()
        print(f"Erro ao assinar o contrato: {error_traceback}")
        return Response({"error": f"Erro ao assinar o contrato: {str(e)}", "traceback": error_traceback}, status=500)

@api_view(['POST'])
def execute_contract_api(request, contract_id):
    try:
        check_connection()
        rental_contract = get_object_or_404(RentalContract, id=contract_id)
        private_key = request.data.get('private_key')

        try:
            account = web3.eth.account.from_key(private_key)
        except ValueError:
            return Response({"error": "Chave privada inválida."}, status=400)

        # Verificar se o endereço é o locador ou o inquilino
        if account.address.lower() != rental_contract.landlord.lower() and account.address.lower() != rental_contract.tenant.lower():
            return Response({"error": "Somente o locador ou o inquilino podem executar o contrato."}, status=403)

        smart_contract = web3.eth.contract(address=Web3.to_checksum_address(rental_contract.contract_address), abi=contract_abi)

        try:
            tx = smart_contract.functions.activateContract().build_transaction({
                'from': account.address,
                'nonce': web3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': web3.to_wei('20', 'gwei')
            })

            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            if tx_receipt['status'] == 1:
                rental_contract.status = 'executed'
                rental_contract.save()

                # Registrar o evento de execução
                ContractEvent.objects.create(
                    contract=rental_contract,
                    event_type='execute',
                    event_data={
                        'tx_hash': tx_hash.hex(),
                        'from_address': account.address,
                        'details': 'Contrato executado.'
                    },
                    tx_hash=tx_hash.hex(),
                    user_address=account.address
                )

                return Response({"message": "Contrato executado com sucesso!", "tx_hash": tx_hash.hex()}, status=200)
            else:
                return Response({"error": "Falha na transação de execução."}, status=500)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# View para registrar pagamento
@api_view(['POST'])
def register_payment_api(request, contract_id):
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

    smart_contract = web3.eth.contract(address=Web3.to_checksum_address(rental_contract.contract_address), abi=contract_abi)

    if payment_type == "Aluguel":
        tx_function = smart_contract.functions.payRent()
    elif payment_type == "Depósito":
        tx_function = smart_contract.functions.payDeposit()
    else:
        return Response({"error": "Tipo de pagamento inválido."}, status=400)

    try:
        tx = tx_function.build_transaction({
            'from': account_to_pay.address,
            'value': web3.to_wei(amount, 'ether'),
            'nonce': web3.eth.get_transaction_count(account_to_pay.address),
            'gas': 200000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt['status'] == 1:
            # Registrar o pagamento no banco de dados
            Payment.objects.create(
                contract=rental_contract,
                amount=amount,
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
                tx_hash=tx_hash.hex(),
                user_address=account_to_pay.address
            )

            return Response({"message": f"Pagamento de {payment_type} registrado com sucesso!", "tx_hash": tx_hash.hex()}, status=200)
        else:
            return Response({"error": "Falha na transação de pagamento."}, status=500)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# View para encerrar contrato
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

            # Registrar o evento de encerramento
            ContractEvent.objects.create(
                contract=rental_contract,
                event_type='terminate',
                event_data={
                    'tx_hash': tx_hash.hex(),
                    'from_address': account_to_terminate.address,
                    'details': 'Contrato encerrado.'
                },
                tx_hash=tx_hash.hex(),
                user_address=account_to_terminate.address
            )

            return Response({"message": "Contrato encerrado com sucesso!", "tx_hash": tx_hash.hex()}, status=200)
        else:
            return Response({"error": "Falha na transação de encerramento."}, status=500)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# View para listar eventos do contrato
@api_view(['GET'])
def contract_events_api(request, contract_id):
    rental_contract = get_object_or_404(RentalContract, id=contract_id)
    events = rental_contract.events.all()
    event_data = [{
        "event_type": event.event_type,
        "tx_hash": event.tx_hash,
        "from_address": event.user_address,
        "event_data": event.event_data,
        "timestamp": event.timestamp,
        "block_number": event.block_number,
        "gas_used": event.gas_used
    } for event in events]
    return Response(event_data)

