import os

from dotenv import load_dotenv  # type:ignore
from web3 import Web3  # type:ignore

load_dotenv()


def check_connection():

    web3 = Web3(Web3.HTTPProvider(os.getenv("SEPOLIA_INFURA_URL")))

    if web3.is_connected():
        # print("Conectado")
        return web3
    else:
        # print("Erro ao conectar")
        raise Exception("Não conectado à rede Ethereum. Verifique sua conexão.")
