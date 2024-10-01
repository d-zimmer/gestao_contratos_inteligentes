from django.shortcuts import render, redirect
from web3 import Web3
from web3 import Account
from dotenv import load_dotenv
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import RentalContract

import os
import json

# Conexão com o Hardhat node
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
    landlord = request.data.get('landlord')
    tenant = request.data.get('tenant')
    rent_amount = request.data.get('rent_amount')
    deposit_amount = request.data.get('deposit_amount')
    private_key = request.data.get('private_key')

    account = Account.from_key(private_key)

    try:
        landlord = Web3.to_checksum_address(landlord)
        tenant = Web3.to_checksum_address(tenant)
    except ValueError:
        return Response({"error": "Endereço inválido"}, status=400)

    tx = contract.functions.createRentalAgreement(
        landlord,
        tenant,
        int(rent_amount),
        int(deposit_amount)
    ).build_transaction({
        'from': account.address,
        'nonce': web3.eth.get_transaction_count(account.address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('20', 'gwei')
    })

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    RentalContract.objects.create(
        landlord=landlord,
        tenant=tenant,
        rent_amount=rent_amount,
        deposit_amount=deposit_amount,
        contract_address=contract_address
    )

    return Response({"message": "Contrato criado com sucesso!", "tx_hash": tx_hash.hex()}, status=201)

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
    tenant_address = request.data.get('tenant_address')
    rent_amount = web3.toWei(request.data.get('rent_amount'), 'ether')

    # Validar o endereço do inquilino
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
    contract = RentalContract.objects.get(tenant=tenant_address)
    Payment.objects.create(
        contract=contract,
        amount=request.data.get('rent_amount'),
        payment_type='rent'
    )

    return Response({"message": "Aluguel pago com sucesso!", "tx_hash": tx_hash.hex()})

@api_view(['POST'])
def sign_contract_api(request):
    contract_id = request.data.get('contract_id')
    private_key = request.data.get('private_key')

    account_to_sign = web3.eth.account.from_key(private_key)

    tx = contract.functions.signAgreement().build_transaction({
        'from': account_to_sign.address,
        'nonce': web3.eth.get_transaction_count(account_to_sign.address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('20', 'gwei')
    })

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    return Response({"message": "Contrato assinado!", "tx_hash": tx_hash.hex()}, status=200)

@api_view(['POST'])
def execute_contract_api(request):
    contract_id = request.data.get('contract_id')
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

    # Função para encerrar o contrato
    tx = contract.functions.terminateContract().build_transaction({
        'from': account_to_terminate.address,
        'nonce': web3.eth.getTransactionCount(account_to_terminate.address),
        'gas': 2000000,
        'gasPrice': web3.toWei('20', 'gwei')
    })

    signed_tx = web3.eth.account.signTransaction(tx, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    receipt = web3.eth.waitForTransactionReceipt(tx_hash)

    # Registrar o encerramento no banco de dados
    contract = RentalContract.objects.get(contract_address=contract_address)
    ContractTermination.objects.create(
        contract=contract,
        terminated_by=account_to_terminate.address
    )

    return Response({"message":"Contrato Encerrado com sucesso!", "tx_hash": tx_hash.hex()}, status=200)
