from django.shortcuts import render, redirect
from .models import RentalContract
from web3 import Web3
import json
from dotenv import load_dotenv
from django.contrib import messages
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import RentalContract

import os

load_dotenv()
private_key = os.getenv("PRIVATE_KEY")

# Conectar ao nó local do Hardhat
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Verificar se a conexão foi estabelecida
if web3.isConnected():
    print("Conectado à rede local do Hardhat")
else:
    print("Erro ao conectar")
    
# Definir o ABI e endereço do contrato após o deploy (substitua por seu ABI e endereço)
with open('\scripts\RentalAgreementABI.json', 'r') as abi_file:
    contract_abi = json.load(abi_file)
    
contract_address = "0x5fbdb2315678afecb367f032d93f642f64180aa3"

# Carregar o contrato
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# API para listar todos os contratos de aluguel
@api_view(['GET'])
def contract_list_api(request):
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
def create_contract_api(request):
    landlord = request.data.get('landlord')
    tenant = request.data.get('tenant')
    rent_amount = request.data.get('rent_amount')
    deposit_amount = request.data.get('deposit_amount')

    # Interagir com o contrato implantado
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    tx_hash = contract.functions.createRentalAgreement(
        Web3.toChecksumAddress(landlord),
        Web3.toChecksumAddress(tenant),
        int(rent_amount),
        int(deposit_amount)
    ).transact({'from': web3.eth.accounts[0]})

    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)  
    contract_address = tx_receipt.contractAddress

    # Criar o contrato no banco de dados
    contract = RentalContract.objects.create(
        landlord=landlord,
        tenant=tenant,
        rent_amount=rent_amount,
        deposit_amount=deposit_amount,
        contract_address=contract_address
    )

    return Response({"message": "Contrato criado com sucesso!"}, status=201)

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
