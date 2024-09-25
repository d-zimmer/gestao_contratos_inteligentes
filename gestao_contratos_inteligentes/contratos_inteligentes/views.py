from django.shortcuts import render, redirect
from .models import RentalContract
from web3 import Web3
from dotenv import load_dotenv
import os

# Carrega as variáveis do .env
load_dotenv()

# Conexão com a blockchain (Sepolia)
web3 = Web3(Web3.HTTPProvider('https://rpc.sepolia.org'))
private_key = os.getenv("PRIVATE_KEY")

# Função para criar o contrato de aluguel
def create_contract(request):
    if request.method == 'POST':
        landlord = request.POST['landlord']
        tenant = request.POST['tenant']
        rent_amount = request.POST['rent_amount']
        deposit_amount = request.POST['deposit_amount']

        # Criar um contrato no banco de dados
        rental_contract = RentalContract(
            landlord=landlord,
            tenant=tenant,
            rent_amount=rent_amount,
            deposit_amount=deposit_amount,
        )
        rental_contract.save()

        # Interação com a blockchain
        # ABI e endereço do contrato (coloque o ABI correto)
        contract_abi = [...]  # ABI gerado na compilação do contrato
        contract_address = '0xEndereçoDoContratoNaBlockchain'  # Endereço do contrato
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)

        # Preparar a transação para deploy do contrato
        tx = contract.functions.createRentalAgreement(
            Web3.toChecksumAddress(landlord),
            Web3.toChecksumAddress(tenant),
            int(rent_amount),
            int(deposit_amount)
        ).buildTransaction({
            'chainId': 11155111,  # ID da Sepolia
            'gas': 2000000,
            'gasPrice': web3.toWei('20', 'gwei'),
            'nonce': web3.eth.getTransactionCount(web3.eth.account.privateKeyToAccount(private_key).address)
        })

        # Assinar e enviar a transação
        signed_tx = web3.eth.account.signTransaction(tx, private_key)
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        web3.eth.waitForTransactionReceipt(tx_hash)

        # Salvar o endereço do contrato no banco de dados
        rental_contract.contract_address = contract_address
        rental_contract.save()

        return redirect('contract_list')

    return render(request, 'create_contract.html')
