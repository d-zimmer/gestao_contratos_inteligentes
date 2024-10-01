import json
import os
from solcx import compile_standard, install_solc

# Instalar a versão do compilador Solidity
install_solc("0.8.18")

# Diretório base (o caminho absoluto da pasta do projeto)
base_path = os.path.dirname(os.path.abspath(__file__))

# Caminho absoluto para o contrato Solidity
solidity_file_path = os.path.join(base_path, "../contracts/RentalAgreement.sol")

# Criar pasta 'build' para armazenar os arquivos compilados, se não existir
build_dir = os.path.join(base_path, "../build")
os.makedirs(build_dir, exist_ok=True)

# Ler o arquivo do contrato Solidity
with open(solidity_file_path, "r") as file:
    rental_agreement_source = file.read()

# Compilar o contrato
compiled_sol = compile_standard(
    {
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
    },
    solc_version="0.8.18",
)

# Escrever a ABI e Bytecode em arquivos JSON dentro da pasta build
compiled_contract_path = os.path.join(build_dir, "compiled_contract.json")
with open(compiled_contract_path, "w") as f:
    json.dump(compiled_sol, f)

abi = compiled_sol["contracts"]["RentalAgreement.sol"]["RentalAgreement"]["abi"]
bytecode = compiled_sol["contracts"]["RentalAgreement.sol"]["RentalAgreement"]["evm"]["bytecode"]["object"]

# Salvar a ABI e o Bytecode em arquivos separados
with open(os.path.join(build_dir, "RentalAgreementABI.json"), "w") as abi_file:
    json.dump(abi, abi_file)

print(f"Compilação concluída. ABI e bytecode gerados em {build_dir}")
