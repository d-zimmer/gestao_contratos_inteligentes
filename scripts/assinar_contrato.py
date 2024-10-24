from web3 import Web3
import os
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

web3 = Web3(Web3.HTTPProvider(os.getenv("GANACHE_URL")))

# Verificar a conexão
if not web3.is_connected():
    raise Exception("Erro ao conectar ao Ganache.")

# Função para carregar o ABI e bytecode do contrato
def load_contract_data():
    with open(os.path.join('build', 'RentalAgreementABI.json'), 'r') as abi_file:
        contract_abi = json.load(abi_file)
    with open(os.path.join('build', 'compiled_contract.json'), 'r') as bytecode_file:
        compiled_contract = json.load(bytecode_file)
        bytecode = compiled_contract["contracts"]["RentalAgreement.sol"]["RentalAgreement"]["evm"]["bytecode"]["object"]
    return contract_abi, bytecode

# Carregar os dados do contrato
contract_abi, bytecode = load_contract_data()

# Exemplo de endereço do contrato já implantado
global_contract_address = Web3.to_checksum_address("0x8fAd8B306d4288527930Ba9d4e4D534F402195D5")
global_contract = web3.eth.contract(address=global_contract_address, abi=contract_abi)

# Função para assinar o contrato como inquilino
def assinar_contrato_inquilino():

    try:
        inquilino_no_contrato = global_contract.functions.inquilino().call()
        locador_no_contrato = global_contract.functions.locador().call()
        print(f"Inquilino registrado no contrato: {inquilino_no_contrato}")
        print(f"Locador registrado no contrato: {locador_no_contrato}")
    except Exception as e:
        print(f"Erro ao consultar o inquilino no contrato: {e}")

    # try:
        # Derivar o endereço da chave privada
    # account_to_sign = web3.eth.account.from_key(private_key)
        # print(f"Endereço derivado da chave privada: {account_to_sign.address}")

        # Verificar se o inquilino está assinando

        # Construir e assinar a transação
        # tx = global_contract.functions.signAgreement().build_transaction({
            # 'from': account_to_sign.address,
            # 'nonce': web3.eth.get_transaction_count(account_to_sign.address),
            # 'gas': 200000,
            # 'gasPrice': web3.to_wei('20', 'gwei')
        # })

        # Assinar e enviar a transação
        # signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        # tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Aguardar confirmação
        # tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        # print(f"Transação bem-sucedida! Hash: {tx_hash.hex()}")

    # except Exception as e:
        # print(f"Erro ao assinar o contrato: {e}")

# Substitua pela chave privada correta do inquilino
# private_key = "0x481e00e2d88759edfcb34edb678bb73bcc74b78b6844fc9fda8b0161bea05ba6"
assinar_contrato_inquilino()
