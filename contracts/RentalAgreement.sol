// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

contract RentalAgreement {
    address public landlord;
    address public tenant;
    uint256 public rentAmount;
    uint256 public deposit;
    bool public isTerminated;
    
    event RentPaid(address indexed tenant, uint256 amount);
    event DepositPaid(address indexed tenant, uint256 amount);
    event ContractTerminated(address indexed landlord, address indexed tenant);

    constructor(uint256 _rentAmount, uint256 _deposit) {
        landlord = msg.sender;
        rentAmount = _rentAmount;
        deposit = _deposit;
        isTerminated = false;
    }

    // Função para criar um contrato de aluguel
    function createRentalAgreement(address _landlord, address _tenant, uint256 _rentAmount, uint256 _deposit) public {
        require(msg.sender == landlord, "Apenas o locador pode criar o contrato.");
        landlord = _landlord;
        tenant = _tenant;
        rentAmount = _rentAmount;
        deposit = _deposit;
        isTerminated = false;
    }

    // Função para pagar o aluguel
    function payRent() public payable {
        require(msg.sender == tenant, "Apenas o inquilino pode pagar o aluguel.");
        require(msg.value == rentAmount, "Valor do aluguel incorreto.");
        require(!isTerminated, "O contrato foi encerrado.");
        
        payable(landlord).transfer(msg.value);
        emit RentPaid(msg.sender, msg.value);
    }

    // Função para pagar o depósito
    function payDeposit() public payable {
        require(msg.sender == tenant, "Apenas o inquilino pode pagar o depósito.");
        require(msg.value == deposit, "Valor do depósito incorreto.");
        require(!isTerminated, "O contrato foi encerrado.");
        
        payable(landlord).transfer(msg.value);
        emit DepositPaid(msg.sender, msg.value);
    }

    // Função para encerrar o contrato
    function terminateContract() public {
        require(msg.sender == landlord, "Apenas o locador pode encerrar o contrato.");
        require(!isTerminated, "O contrato já foi encerrado.");
        
        isTerminated = true;
        emit ContractTerminated(landlord, tenant);
    }

    // Função para verificar se o contrato está ativo
    function isContractActive() public view returns (bool) {
        return !isTerminated;
    }
}
