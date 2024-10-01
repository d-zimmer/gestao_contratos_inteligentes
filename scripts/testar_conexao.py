from web3 import Web3

web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

if web3.is_connected():
    print("Conectado à blockchain local")
else:
    print("Falha ao conectar")
