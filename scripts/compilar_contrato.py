import json
import os
from solcx import compile_standard, install_solc

# Instalar a versão do compilador Solidity
install_solc("0.8.18")

# Diretório base (o caminho absoluto da pasta do projeto)
base_path = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(base_path, "../build")
os.makedirs(build_dir, exist_ok=True)

# Ler o arquivo do contrato Solidity
with open("contracts/RentalAgreement.sol", "r") as file:
    rental_agreement_source = file.read()

compiled_sol = compile_standard({
    "language": "Solidity",
    "sources": {
        "RentalAgreement.sol": {
            "content": rental_agreement_source
        }
    },
    "settings": {
        "outputSelection": {
            "*": {
                "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
            }
        }
    }
}, solc_version="0.8.18")

# Escrever a ABI e Bytecode em arquivos JSON dentro da pasta build
with open("build/compiled_contract.json", "w") as f:
    json.dump(compiled_sol, f)

with open("build/RentalAgreementABI.json", "w") as abi_file:
    abi = compiled_sol["contracts"]["RentalAgreement.sol"]["RentalAgreement"]["abi"]
    json.dump(abi, abi_file)

print("Contrato compilado com sucesso.")
