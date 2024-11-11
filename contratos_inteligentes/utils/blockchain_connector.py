import os
from web3 import Web3  # type: ignore
from eth_tester import EthereumTester, PyEVMBackend  # type: ignore
from eth_utils import to_wei
from web3.providers.eth_tester import EthereumTesterProvider  # type: ignore

class BlockchainConnector:
    def __init__(self):
        self.web3 = None

    def connect(self):
        if os.getenv("TEST_ENV") == "true":
            # Inicialize o EthereumTester com PyEVMBackend
            tester = EthereumTester(backend=PyEVMBackend())

            # Inicializa Web3 com o EthereumTesterProvider
            self.web3 = Web3(EthereumTesterProvider(tester))

            # Definir as chaves privadas e garantir que as contas tenham saldo
            landlord_private_key = "0x851e3cf1a6db1937de7ab71ee0ec25607649d87184d6e5cf199ce72c2263c45c"
            tenant_private_key = "0x5990c131de45024a70bed095da1e58a48972ed815694719b4f251a8b6d59e24b"

            # Adicionar as contas customizadas ao EthereumTester
            landlord_address = tester.add_account(landlord_private_key)
            tenant_address = tester.add_account(tenant_private_key)

            # Transferir saldo para as contas landlord e tenant
            tester.send_transaction({
                "from": tester.get_accounts()[0],  # Conta base do EthereumTester
                "to": landlord_address,
                "value": to_wei(100, "ether"),
                "gas": 21000,
            })
            tester.send_transaction({
                "from": tester.get_accounts()[0],  # Conta base do EthereumTester
                "to": tenant_address,
                "value": to_wei(100, "ether"),
                "gas": 21000,
            })

            # Confirmação de saldo
            if self.web3.eth.get_balance(landlord_address) == 0 or self.web3.eth.get_balance(tenant_address) == 0:
                raise Exception("Falha ao configurar saldo para contas de teste no ambiente PyEVM.")

        else:
            # Conectar à rede Sepolia ou outra rede real
            sepolia_url = os.getenv("GANACHE_URL")
            self.web3 = Web3(Web3.HTTPProvider(sepolia_url))

        if not self.web3.is_connected():
            raise Exception("Não conectado à rede Ethereum. Verifique sua conexão.")
        
        return self.web3

    def get_web3_instance(self):
        if not self.web3:
            self.connect()
        return self.web3
