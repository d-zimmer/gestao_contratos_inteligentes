from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from web3 import Web3, Account
from .models import RentalContract, Payment, ContractTermination, ContractEvent
from django.utils import timezone 
import os
import json

# Função para carregar o ABI e bytecode do contrato inteligente
def load_contract_data():
    with open(os.path.join('build', 'RentalAgreementABI.json'), 'r') as abi_file:
        contract_abi = json.load(abi_file)
    with open(os.path.join('build', 'compiled_contract.json'), 'r') as bytecode_file:
        compiled_contract = json.load(bytecode_file)
        bytecode = compiled_contract["contracts"]["RentalAgreement.sol"]["RentalAgreement"]["evm"]["bytecode"]["object"]
    return contract_abi, bytecode

# Função para verificar a conexão com o nó Ethereum
def check_connection():
    if not web3.is_connected():
        raise Exception("Não conectado à rede Ethereum. Verifique sua conexão.")

web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

# Verificar se a conexão foi estabelecida
if web3.is_connected():
    print("Conectado à rede local Ganache")
else:
    print("Erro ao conectar")

# Definir o ABI e o endereço do contrato
with open(os.path.join('build', 'RentalAgreementABI.json'), 'r') as abi_file:
    contract_abi = json.load(abi_file)

contract_address = Web3.to_checksum_address("0x5fbdb2315678afecb367f032d93f642f64180aa3")

# Carregar o contrato inteligente
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# View para listar todos os contratos
@api_view(['GET'])
def contract_list_api(request):
    contracts = RentalContract.objects.all()
    contracts_data = [{
        "id": contract.id,
        "landlord": contract.landlord,
        "tenant": contract.tenant,
        "rent_amount": contract.rent_amount,
        "deposit_amount": contract.deposit_amount,
        "contract_address": contract.contract_address,
        "created_at": contract.created_at
    } for contract in contracts]
    return Response(contracts_data)

# View para criar um novo contrato
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

    if not rent_amount or not deposit_amount or int(rent_amount) <= 0 or int(deposit_amount) <= 0:
        return Response({"error": "Valores de aluguel ou depósito inválidos"}, status=400)

    account = web3.eth.account.from_key(private_key)

    try:
        landlord = Web3.to_checksum_address(landlord)
        tenant = Web3.to_checksum_address(tenant)
    except ValueError:
        return Response({"error": "Endereço inválido"}, status=400)

    contract_abi, bytecode = load_contract_data()

    contract = web3.eth.contract(abi=contract_abi, bytecode=bytecode)

    try:
        transaction = contract.constructor(int(rent_amount), int(deposit_amount)).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': 2000000,
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

# View para pagar aluguel
@api_view(['POST'])
def pay_rent_api(request, contract_id):
    try:
        check_connection()
        
        contract = get_object_or_404(RentalContract, id=contract_id)
        tenant_address = request.data.get('tenant_address')
        rent_amount = web3.toWei(request.data.get('rent_amount'), 'ether')

        if not Web3.is_address(tenant_address):
            return Response({"error": "Endereço do inquilino inválido"}, status=400)
        
        tenant_address = Web3.to_checksum_address(tenant_address)

        tx_hash = contract.functions.payRent().transact({
            'from': tenant_address,
            'value': rent_amount
        })

        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

        Payment.objects.create(
            contract=contract,
            amount=request.data.get('rent_amount'),
            payment_type='rent',
            transaction_hash=tx_hash.hex(),
            is_verified=True
        )

        return Response({"message": "Aluguel pago com sucesso!", "tx_hash": tx_hash.hex()})

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def sign_contract_api(request, contract_id):
    # Busca o contrato pelo ID
    contract = get_object_or_404(RentalContract, id=contract_id)
    private_key = request.data.get('private_key')
    user_type = request.data.get('user_type')

    # Obter o endereço da conta que está assinando
    account_to_sign = web3.eth.account.from_key(private_key)

    # Carregar o contrato inteligente da blockchain usando o endereço do contrato
    blockchain_contract = web3.eth.contract(address=contract.contract_address, abi=contract_abi)

    # Verificar quem está assinando (locador ou inquilino) e atualizar a assinatura
    if user_type == 'landlord':
        contract.landlord_signature = account_to_sign.address
        print(f"Locador assinou o contrato. Endereço da assinatura: {contract.landlord_signature}")
    elif user_type == 'tenant':
        contract.tenant_signature = account_to_sign.address
        print(f"Inquilino assinou o contrato. Endereço da assinatura: {contract.tenant_signature}")
    else:
        return Response({"error": "Tipo de usuário inválido."}, status=400)

    # Verificar se ambas as assinaturas foram feitas
    if contract.is_fully_signed():
        contract.status = 'active'
        print(f"Contrato {contract_id} foi completamente assinado. Status atualizado para 'ativo'.")

    # Registrar o estado do contrato antes de salvar
    print(f"Estado do contrato antes de salvar: Locador: {contract.landlord_signature}, Inquilino: {contract.tenant_signature}, Status: {contract.status}")

    try:
        # Salvar o contrato com as assinaturas no banco de dados
        contract.save()

        # Registrar no log após salvar
        print(f"Contrato {contract_id} salvo no banco de dados com as assinaturas.")

        # Realizar a transação na blockchain para assinar o contrato
        tx = blockchain_contract.functions.signAgreement().build_transaction({
            'from': account_to_sign.address,
            'nonce': web3.eth.get_transaction_count(account_to_sign.address),
            'gas': 2000000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)

        # Registrar o evento da transação
        ContractEvent.objects.create(
            contract=contract,
            event_type='sign',
            event_data={'tx_hash': tx_hash.hex()},
            timestamp=timezone.now()
        )

        # Retornar sucesso
        return Response({
            "message": "Contrato assinado com sucesso!",
            "tx_hash": tx_hash.hex(),
            "status": contract.status
        }, status=200)
    except Exception as e:
        print(f"Erro ao salvar ou processar a assinatura: {str(e)}")
        return Response({"error": str(e)}, status=500)

# View para executar contrato
@api_view(['POST'])
def execute_contract_api(request, contract_id):
    try:
        check_connection()
        contract = get_object_or_404(RentalContract, id=contract_id)
        private_key = request.data.get('private_key')

        account = Account.from_key(private_key)

        tx = contract.functions.activateContract().build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': 2000000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)

        return Response({"message": "Contrato executado!", "tx_hash": tx_hash.hex()}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# View para registrar pagamento
@api_view(['POST'])
def register_payment_api(request, contract_id):
    contract = get_object_or_404(RentalContract, id=contract_id)
    private_key = request.data.get('private_key')
    payment_type = request.data.get('payment_type')
    amount = request.data.get('amount')

    account_to_pay = web3.eth.account.privateKeyToAccount(private_key)

    if payment_type == "Aluguel":
        tx_function = contract.functions.payRent()
    elif payment_type == "Depósito":
        tx_function = contract.functions.payDeposit()

    tx = tx_function.build_transaction({
        'from': account_to_pay.address,
        'value': web3.to_wei(amount, 'ether'),
        'nonce': web3.eth.get_transaction_count(account_to_pay.address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('20', 'gwei')
    })

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    return Response({"message": f"{payment_type} registrado com sucesso!", "tx_hash": tx_hash.hex()}, status=200)

# View para encerrar contrato
@api_view(['POST'])
def terminate_contract_api(request, contract_id):
    contract = get_object_or_404(RentalContract, id=contract_id)
    private_key = request.data.get('private_key')

    account_to_terminate = web3.eth.account.from_key(private_key)

    try:
        tx = contract.functions.terminateContract().build_transaction({
            'from': account_to_terminate.address,
            'nonce': web3.eth.get_transaction_count(account_to_terminate.address),
            'gas': 2000000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        ContractTermination.objects.create(
            contract=contract,
            terminated_by=account_to_terminate.address,
            termination_transaction_hash=tx_hash.hex()
        )

        contract.status = 'terminated'
        contract.save()

        return Response({"message": "Contrato Encerrado com sucesso!", "tx_hash": tx_hash.hex()})

    except Exception as e:
        return Response({"error": str(e)}, status=500)
