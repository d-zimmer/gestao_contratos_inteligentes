from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.http import JsonResponse # type: ignore
from web3 import Web3, Account # type: ignore
from dotenv import load_dotenv # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.decorators import api_view # type: ignore
from .models import RentalContract, User

import os
import json

def load_contract_data():
    with open(os.path.join('build', 'RentalAgreementABI.json'), 'r') as abi_file:
        contract_abi = json.load(abi_file)

    with open(os.path.join('build', 'compiled_contract.json'), 'r') as bytecode_file:
        compiled_contract = json.load(bytecode_file)
        bytecode = compiled_contract["contracts"]["RentalAgreement.sol"]["RentalAgreement"]["evm"]["bytecode"]["object"]

    return contract_abi, bytecode

def check_connection():
    if not web3.is_connected():
        raise Exception("Não conectado à rede Ethereum. Verifique sua conexão.")

web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

# Verificar se a conexão foi estabelecida
if web3.is_connected():
    print("Conectado à rede local Ganache")
else:
    print("Erro ao conectar")

# Definir o ABI e endereço do contrato após o deploy
with open(os.path.join('build', 'RentalAgreementABI.json'), 'r') as abi_file:
    contract_abi = json.load(abi_file)

contract_address = Web3.to_checksum_address("0x5fbdb2315678afecb367f032d93f642f64180aa3")

# Carregar o contrato
contract = web3.eth.contract(address=contract_address, abi=contract_abi) 

@api_view(['POST'])
def create_contract_api(request):
    try:
        check_connection()
    except Exception as e:
        return Response({"error": "Falha na conexão com a rede Ethereum: " + str(e)}, status=500)  # Retorna a mensagem de erro

    landlord = request.data.get('landlord')
    tenant = request.data.get('tenant')
    rent_amount = request.data.get('rent_amount')
    deposit_amount = request.data.get('deposit_amount')
    private_key = request.data.get('private_key')

    if not rent_amount or not deposit_amount or int(rent_amount) <= 0 or int(deposit_amount) <= 0:
        return Response({"error": "Valores de aluguel ou depósito inválidos"}, status=400)

    # Carregar a conta a partir da chave privada
    account = web3.eth.account.from_key(private_key)

    try:
        # Validar endereços
        landlord = Web3.to_checksum_address(landlord)
        tenant = Web3.to_checksum_address(tenant)
    except ValueError:
        return Response({"error": "Endereço inválido"}, status=400)

    # Carregar ABI e bytecode através da função auxiliar
    contract_abi, bytecode = load_contract_data()

    # Fazer o deploy de um novo contrato inteligente para cada novo contrato de aluguel
    contract = web3.eth.contract(abi=contract_abi, bytecode=bytecode)

    try:
        transaction = contract.constructor(int(rent_amount), int(deposit_amount)).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': 2000000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        # Assinar e enviar a transação
        signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Esperar pelo recibo do deploy do contrato
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        new_contract_address = tx_receipt.contractAddress  # Endereço do novo contrato

        # Salvar no banco de dados o novo contrato, inicializando o status como 'pending'
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
        "created_at": contract.created_at  # Adicionando a data
    } for contract in contracts]

    return Response(contracts_data)

@api_view(['POST'])
def pay_rent_api(request):
    try:
        check_connection()  # Verifica a conexão antes de processar a transação
        
        tenant_address = request.data.get('tenant_address')
        rent_amount = web3.toWei(request.data.get('rent_amount'), 'ether')
        private_key = request.data.get('private_key')

        if not Web3.is_address(tenant_address):
            return Response({"error": "Endereço do inquilino inválido"}, status=400)
        
        tenant_address = Web3.to_checksum_address(tenant_address)

        # Enviar a transação para o contrato
        tx_hash = contract.functions.payRent().transact({
            'from': tenant_address,
            'value': rent_amount
        })

        # Esperar o recibo da transação
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

        # Registrar o pagamento no banco de dados
        contract = get_object_or_404(RentalContract, tenant=tenant_address)
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
def sign_contract_api(request):
    contract_id = request.data.get('contract_id')
    private_key = request.data.get('private_key')
    user_type = request.data.get('user_type')  # landlord ou tenant

    contract = get_object_or_404(RentalContract, id=contract_id)
    account_to_sign = web3.eth.account.from_key(private_key)

    # Verificar quem está assinando
    if user_type == 'landlord':
        contract.landlord_signature = account_to_sign.address
    elif user_type == 'tenant':
        contract.tenant_signature = account_to_sign.address

    # Verificar se ambas as assinaturas foram feitas
    if contract.is_fully_signed():
        contract.status = 'active'  # Mudar status para ativo se ambas as partes assinaram

    contract.save()

    # Realizar a transação na blockchain
    tx = contract.functions.signAgreement().build_transaction({
        'from': account_to_sign.address,
        'nonce': web3.eth.get_transaction_count(account_to_sign.address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('20', 'gwei')
    })

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    return Response({"message": "Contrato assinado!", "tx_hash": tx_hash.hex(), "status": contract.status}, status=200)

@api_view(['POST'])
def execute_contract_api(request):
    try:
        check_connection()
        contract_id = request.data.get('contract_id')
        private_key = request.data.get('private_key')

        account = Account.from_key(private_key)

        tx = contract.functions.activateContract().build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),  # Sempre verificar conexão antes
            'gas': 2000000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)

        return Response({"message": "Contrato executado!", "tx_hash": tx_hash.hex()}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def register_payment_api(request):
    contract_id = request.data.get('contract_id')
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

@api_view(['POST'])
def terminate_contract_api(request):
    contract_id = request.data.get('contract_id')
    private_key = request.data.get('private_key')

    account_to_terminate = web3.eth.account.from_key(private_key)

    contract = get_object_or_404(RentalContract, id=contract_id)

    try:
        # Função para encerrar o contrato
        tx = contract.functions.terminateContract().build_transaction({
            'from': account_to_terminate.address,
            'nonce': web3.eth.get_transaction_count(account_to_terminate.address),
            'gas': 2000000,
            'gasPrice': web3.to_wei('20', 'gwei')
        })

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        # Registrar o encerramento no banco de dados
        ContractTermination.objects.create(
            contract=contract,
            terminated_by=account_to_terminate.address,
            termination_transaction_hash=tx_hash.hex()
        )

        contract.status = 'terminated'
        contract.save()

        return Response({"message": "Contrato Encerrado com sucesso!", "tx_hash": tx_hash.hex()}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
