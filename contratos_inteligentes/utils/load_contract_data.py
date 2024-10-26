import json
import os


def load_contract_data():
    with open(os.path.join("build", "RentalAgreementABI.json"), "r") as abi_file:
        contract_abi = json.load(abi_file)
    with open(os.path.join("build", "compiled_contract.json"), "r") as bytecode_file:
        compiled_contract = json.load(bytecode_file)
        bytecode = compiled_contract["contracts"]["RentalAgreement.sol"][
            "RentalAgreement"
        ]["evm"]["bytecode"]["object"]
    return contract_abi, bytecode
