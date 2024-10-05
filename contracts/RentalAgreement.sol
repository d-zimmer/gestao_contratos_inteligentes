// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

contract RentalAgreement {
    address public locador;
    address public inquilino;
    uint256 public rentAmount;
    uint256 public deposit;
    bool public isTerminated;
    bool public locadorSigned;
    bool public inquilinoSigned;
    
    event RentPaid(address indexed inquilino, uint256 amount);
    event DepositPaid(address indexed inquilino, uint256 amount);
    event ContractTerminated(address indexed locador, address indexed inquilino);
    event AgreementSigned(address signer);

    constructor(uint256 _rentAmount, uint256 _deposit) {
        locador = msg.sender;
        rentAmount = _rentAmount;
        deposit = _deposit;
        isTerminated = false;
    }
    // Função para criar um contrato de aluguel
    function createRentalAgreement(address _locador, address _inquilino, uint256 _rentAmount, uint256 _deposit) public {
        require(msg.sender == locador, "apenas o locador pode criar o contrato.");
        locador = _locador;
        inquilino = _inquilino;
        rentAmount = _rentAmount;
        deposit = _deposit;
        isTerminated = false;
    }

    // Função para pagar o aluguel
    function payRent() public payable {
        require(msg.sender == inquilino, "apenas o inquilino pode pagar o aluguel.");
        require(msg.value == rentAmount, "Valor do aluguel incorreto.");
        require(!isTerminated, "O contrato foi encerrado.");
        
        payable(locador).transfer(msg.value);
        emit RentPaid(msg.sender, msg.value);
    }

    // Função para pagar o depósito
    function payDeposit() public payable {
        require(msg.sender == inquilino, "apenas o inquilino pode pagar o deposito.");
        require(msg.value == deposit, "Valor do deposito incorreto.");
        require(!isTerminated, "O contrato foi encerrado.");
        
        payable(locador).transfer(msg.value);
        emit DepositPaid(msg.sender, msg.value);
    }

    // Função para encerrar o contrato
    function terminateContract() public {
        require(msg.sender == locador, "apenas o locador pode encerrar o contrato.");
        require(!isTerminated, "O contrato ja foi encerrado.");
        
        isTerminated = true;
        emit ContractTerminated(locador, inquilino);
    }

    function signAgreement() public {
        if (msg.sender == locador) {
            require(!locadorSigned, "Locador already signed.");
            locadorSigned = true;
            emit AgreementSigned(msg.sender);
        } else if (msg.sender == inquilino) {
            require(!inquilinoSigned, "Inquilino already signed.");
            inquilinoSigned = true;
            emit AgreementSigned(msg.sender);
        } else {
            revert("Only locador or inquilino can sign the agreement.");
        }
    }


    function isFullySigned() public view returns (bool) {
        return locadorSigned && inquilinoSigned;
    }

    // Função para verificar se o contrato está ativo
    function isContractActive() public view returns (bool) {
        return !isTerminated;
    }
}
