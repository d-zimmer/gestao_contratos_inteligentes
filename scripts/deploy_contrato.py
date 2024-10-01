from web3 import Web3
import json
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente (como as chaves privadas)
load_dotenv()

# Conectar ao nó local do blockchain (Hardhat ou Ganache)
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

if web3.is_connected():
    print("Conectado à blockchain local")

# Carregar a chave privada do arquivo .env
private_key = os.getenv("PRIVATE_KEY")
account = web3.eth.account.from_key(private_key)
account_address = account.address

# Carregar o ABI e o bytecode do contrato compilado
with open("build/contract_abi.json", "r") as abi_file:  # Correção: caminho correto para o arquivo
    contract_abi = json.load(abi_file)

with open("build/compiled_contract.json", "r") as bytecode_file:  # Correção: modo "r" para leitura
    compiled_contract = json.load(bytecode_file)
    bytecode = compiled_contract["contracts"]["RentalAgreement.sol"]["RentalAgreement"]["evm"]["bytecode"]["object"]

# Definir o contrato
RentalAgreement = web3.eth.contract(abi=contract_abi, bytecode=bytecode)

# Construir a transação de deploy
transaction = RentalAgreement.constructor(1500, 3000).build_transaction({
    "from": account_address,
    "nonce": web3.eth.get_transaction_count(account_address),
    "gasPrice": web3.to_wei("20", "gwei"),
    "gas": 2000000
})

# Assinar a transação
signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

# Enviar a transação para a rede
tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

# Esperar pelo recibo
tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

print(f"Contrato implantado em: {tx_receipt.contractAddress}")
