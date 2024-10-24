from web3 import Web3
import os
import json
from dotenv import load_dotenv

load_dotenv()

GANACHE_URL = os.getenv("GANACHE_URL")
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if not web3.is_connected():
    raise Exception("Erro ao conectar ao Ganache.")

def load_contract_data():
    with open(os.path.join('build', 'RentalAgreementABI.json'), 'r') as abi_file:
        contract_abi = json.load(abi_file)
    with open(os.path.join('build', 'compiled_contract.json'), 'r') as bytecode_file:
        compiled_contract = json.load(bytecode_file)
        bytecode = compiled_contract["contracts"]["RentalAgreement.sol"]["RentalAgreement"]["evm"]["bytecode"]["object"]
    return contract_abi, bytecode

def normalize_address(address):
    if not address:
        raise ValueError("Endereço não pode ser None ou vazio.")
    try:
        return Web3.to_checksum_address(address)
    except ValueError:
        raise ValueError(f"Endereço inválido: {address}")

contract_abi, bytecode = load_contract_data()

global_contract_address = Web3.to_checksum_address("0xD4Bc91b48F7c4eC4001846DbCAbA7067CbC83987")
global_contract = web3.eth.contract(address=global_contract_address, abi=contract_abi)

try:
    locador = global_contract.functions.locador().call()
    print(f"Locador: {locador}")
except Exception as e:
    print(f"Erro ao consultar o locador: {e}")

print("Contrato carregado com sucesso")
