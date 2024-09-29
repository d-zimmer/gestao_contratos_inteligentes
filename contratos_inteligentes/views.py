from django.shortcuts import render, redirect
from web3 import Web3
# from web3.middleware import geth_poa_middleware
from web3.auto.gethdev import w3
from web3 import Account
from dotenv import load_dotenv
from django.contrib import messages
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import RentalContract

import os
import json

load_dotenv()

web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Verificar se a conexão foi estabelecida
if web3.is_connected():
    print("Conectado à rede local do Hardhat")
else:
    print("Erro ao conectar")

# Carregar a chave privada do arquivo .env
private_key = os.getenv("PRIVATE_KEY")
account = Account.from_key(private_key)

# Definir o ABI e endereço do contrato após o deploy (substitua por seu ABI e endereço)
with open('scripts/RentalAgreementABI.json', 'r') as abi_file:
    contract_abi = json.load(abi_file)

contract_address = Web3.to_checksum_address("0x5fbdb2315678afecb367f032d93f642f64180aa3")

# Carregar o contrato
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

@api_view(['POST'])
def create_contract(request):
    landlord = request.data.get('landlord')
    tenant = request.data.get('tenant')
    rent_amount = request.data.get('rent_amount')
    deposit_amount = request.data.get('deposit_amount')

    # Interagir com o contrato inteligente
    tx = contract.functions.createRentalAgreement(
        Web3.toChecksumAddress(landlord),
        Web3.toChecksumAddress(tenant),
        int(rent_amount),
        int(deposit_amount)
    ).buildTransaction({
        'from': account.address,
        'nonce': web3.eth.getTransactionCount(account.address),
        'gas': 2000000,
        'gasPrice': web3.toWei('20', 'gwei')
    })

    # Assinar e enviar a transação
    signed_tx = web3.eth.account.signTransaction(tx, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    receipt = web3.eth.waitForTransactionReceipt(tx_hash)

    # Salvar o contrato no banco de dados
    RentalContract.objects.create(
        landlord=landlord,
        tenant=tenant,
        rent_amount=rent_amount,
        deposit_amount=deposit_amount,
        contract_address=contract_address
    )

    return Response({"message": "Contrato criado com sucesso!", "tx_hash": tx_hash.hex()}, status=201)

@api_view(['GET'])
def contract_list(request):
    contracts = RentalContract.objects.all()
    contracts_data = [{
        "landlord": contract.landlord,
        "tenant": contract.tenant,
        "rent_amount": contract.rent_amount,
        "deposit_amount": contract.deposit_amount,
        "contract_address": contract.contract_address
    } for contract in contracts]

    return Response(contracts_data)

@api_view(['POST'])
def pay_rent(request):
    tenant_address = request.data.get('tenant_address')
    rent_amount = web3.toWei(request.data.get('rent_amount'), 'ether')

    # Enviar a transação para o contrato
    tx_hash = contract.functions.payRent().transact({
        'from': Web3.toChecksumAddress(tenant_address),
        'value': rent_amount
    })

    # Esperar o recibo da transação
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

    return Response({"message": "Aluguel pago com sucesso!", "tx_hash": tx_hash.hex()})

@api_view(['POST'])
def sign_contract(request):
    contract_id = request.data.get('contract_id')
    private_key = request.data.get('private_key')  # Recebe a chave privada do locador/inquilino

    # Acessar o contrato com a chave privada fornecida
    account_to_sign = web3.eth.account.privateKeyToAccount(private_key)

    # Exemplo: registrar uma assinatura no contrato (dependendo da lógica do contrato)
    tx = contract.functions.signAgreement().buildTransaction({
        'from': account_to_sign.address,
        'nonce': web3.eth.getTransactionCount(account_to_sign.address),
        'gas': 2000000,
        'gasPrice': web3.toWei('20', 'gwei')
    })

    # Assinar e enviar a transação
    signed_tx = web3.eth.account.signTransaction(tx, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    receipt = web3.eth.waitForTransactionReceipt(tx_hash)

    return Response({"message": "Contrato assinado!", "tx_hash": tx_hash.hex()}, status=200)

@api_view(['POST'])
def execute_contract(request):
    contract_id = request.data.get('contract_id')

    # Lógica para ativar/executar o contrato na blockchain
    tx = contract.functions.activateContract().buildTransaction({
        'from': account.address,
        'nonce': web3.eth.getTransactionCount(account.address),
        'gas': 2000000,
        'gasPrice': web3.toWei('20', 'gwei')
    })

    signed_tx = web3.eth.account.signTransaction(tx, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    receipt = web3.eth.waitForTransactionReceipt(tx_hash)

    return Response({"message": "Contrato executado!", "tx_hash": tx_hash.hex()}, status=200)

@api_view(['POST'])
def register_payment(request):
    contract_id = request.data.get('contract_id')
    private_key = request.data.get('private_key')
    payment_type = request.data.get('payment_type')
    amount = request.data.get('amount')

    # Escolher a função de pagamento (aluguel ou depósito)
    if payment_type == "Aluguel":
        tx_function = contract.functions.payRent()
    elif payment_type == "Depósito":
        tx_function = contract.functions.payDeposit()

    # Preparar a transação
    account_to_pay = web3.eth.account.privateKeyToAccount(private_key)
    tx = tx_function.buildTransaction({
        'from': account_to_pay.address,
        'value': web3.toWei(amount, 'ether'),
        'nonce': web3.eth.getTransactionCount(account_to_pay.address),
        'gas': 2000000,
        'gasPrice': web3.toWei('20', 'gwei')
    })

    signed_tx = web3.eth.account.signTransaction(tx, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    receipt = web3.eth.waitForTransactionReceipt(tx_hash)

    return Response({"message": f"{payment_type} registrado com sucesso!", "tx_hash": tx_hash.hex()}, status=200)

@api_view(['POST'])
def terminate_contract(request):
    contract_id = request.data.get('contract_id')
    private_key = request.data.get('private_key')

    account_to_terminate = web3.eth.account.privateKeyToAccount(private_key)

    # Função para encerrar o contrato
    tx = contract.functions.terminateContract().buildTransaction({
        'from': account_to_terminate.address,
        'nonce': web3.eth.getTransactionCount(account_to_terminate.address),
        'gas': 2000000,
        'gasPrice': web3.toWei('20', 'gwei')
    })

    signed_tx = web3.eth.account.signTransaction(tx, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    receipt = web3.eth.waitForTransactionReceipt(tx_hash)

    return Response({"message":"Contrato Encerrado com sucesso!", "tx_hash": tx_hash.hex()}, status=200)
