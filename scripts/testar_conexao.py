from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()

GANACHE_URL = os.getenv("SEPOLIA_INFURA_URL")
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if web3.is_connected():
    print("Conectado à rede local Ganache")
else:
    print("Erro ao conectar à rede Ganache")
