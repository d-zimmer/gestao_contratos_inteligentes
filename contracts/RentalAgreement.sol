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

    constructor(address _inquilino, uint256 _rentAmount, uint256 _deposit) {
        locador = msg.sender;
        inquilino = _inquilino; // Vincular o inquilino ao contrato
        rentAmount = _rentAmount;
        deposit = _deposit;
        isTerminated = false;
    }

    function setInquilino(address _inquilino) public {
        require(msg.sender == locador, unicode"Apenas o locador pode definir o inquilino.");
        require(_inquilino != address(0), unicode"O endereço do inquilino não pode ser o endereço zero.");
        inquilino = _inquilino;
    }

    function activateContract() public {
        require(msg.sender == locador || msg.sender == inquilino, unicode"Apenas o locador ou o inquilino podem ativar o contrato.");
        require(!isActive, unicode"O contrato já está ativo.");
        require(isFullySigned(), unicode"O contrato precisa ser totalmente assinado antes de ser ativado.");
        
        isActive = true;  // Ativar o contrato
        emit ContractActivated(msg.sender);
    }

    function payRent() public payable {
        require(msg.sender == inquilino, unicode"Apenas o inquilino pode pagar o aluguel.");
        require(msg.value == rentAmount, unicode"Valor do aluguel incorreto.");
        require(!isTerminated, unicode"O contrato foi encerrado.");
        require(isFullySigned(), unicode"O contrato precisa ser assinado por ambas as partes antes de realizar pagamentos.");

        payable(locador).transfer(msg.value);
        emit RentPaid(msg.sender, msg.value);
    }

    // Função para pagar o depósito
    function payDeposit() public payable {
        require(msg.sender == inquilino, unicode"Apenas o inquilino pode pagar o deposito.");
        require(msg.value == deposit, unicode"Valor do deposito incorreto.");
        require(!isTerminated, unicode"O contrato foi encerrado.");
        require(isFullySigned(), unicode"O contrato precisa ser assinado por ambas as partes antes de realizar pagamentos.");
        
        payable(locador).transfer(msg.value);
        emit DepositPaid(msg.sender, msg.value);
    }

    // Função para encerrar o contrato
    function terminateContract() public {
        require(msg.sender == locador, unicode"Apenas o locador pode encerrar o contrato.");
        require(!isTerminated, unicode"O contrato ja foi encerrado.");
        
        isTerminated = true;
        emit ContractTerminated(locador, inquilino);
    }

    event DebugSender(address sender);

    function signAgreement() public {
        require(!isTerminated, unicode"O contrato foi encerrado.");
        require(!isFullySigned(), unicode"O contrato já foi totalmente assinado.");

        if (msg.sender == locador) {
            require(!locadorSigned, unicode"Locador já assinou.");
            locadorSigned = true;
            emit AgreementSigned(msg.sender);
        } else if (msg.sender == inquilino) {
            require(!inquilinoSigned, unicode"Inquilino já assinou.");
            inquilinoSigned = true;
            emit AgreementSigned(msg.sender);
        } else {
            revert(unicode"Somente locador ou inquilino podem assinar o contrato.");
        }
    }

    function isFullySigned() public view returns (bool) {
        return locadorSigned && inquilinoSigned;
    }

    function isContractActive() public view returns (bool) {
        return !isTerminated;
    }
}
