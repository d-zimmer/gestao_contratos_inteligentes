from web3 import Web3  # type:ignore

def normalize_address(address):
    if address is None or address == "":  # Verifica se o endereço é None ou uma string vazia
        raise ValueError("Endereço não pode ser None ou vazio.")
    try:
        return Web3.to_checksum_address(address)
    except ValueError:
        raise ValueError(f"Endereço inválido: {address}")