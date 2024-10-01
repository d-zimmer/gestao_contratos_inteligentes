from web3 import Web3

# Conectar ao nó local do blockchain (Hardhat ou Ganache)
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Gerar 5 novas contas
for i in range(5):
    account = web3.eth.account.create()
    print(f"Account #{i+1}:")
    print(f"Address: {account.address}")
    print(f"Private Key: {account.key.hex()}")
