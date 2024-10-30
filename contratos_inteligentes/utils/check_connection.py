# check_connection.py
from .blockchain_connector import BlockchainConnector

def check_connection():
    connector = BlockchainConnector()
    return connector.get_web3_instance()
