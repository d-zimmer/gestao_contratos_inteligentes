from web3 import Web3
from django.http import JsonResponse

# Conectar à rede Sepolia
web3 = Web3(Web3.HTTPProvider('https://rpc.sepolia.org'))

# Endereço do contrato e ABI (obtido após o deploy com Hardhat)
contract_address = '0xSEU_CONTRATO_ADRESS'
contract_abi = [ABI_DO_CONTRATO]  # ABI gerado pelo Hardhat

# Conectando ao contrato
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

def pay_rent_view(request):
    # Exemplo de função que chama o contrato para pagar aluguel
    tx_hash = contract.functions.payRent().transact({
        'from': web3.eth.accounts[0],  # Endereço do pagador
        'value': web3.toWei(1, 'ether')  # Valor do aluguel
    })
    receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    return JsonResponse({'status': 'Rent paid', 'receipt': str(receipt)})
