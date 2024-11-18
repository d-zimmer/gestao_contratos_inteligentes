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
    bool public isActive;
    uint256 public dataVencimentoAluguel;
    uint256 public dataTerminoContrato;
    uint256 public duracaoContratoSegundos;
    uint256 public startTimestamp;
    uint256 public endTimestamp;

    event RentPaid(address indexed inquilino, uint256 amount);
    event DepositPaid(address indexed inquilino, uint256 amount);
    event ContractTerminated(address indexed locador, address indexed inquilino);
    event AgreementSigned(address signer);
    event ContractRenewed(address indexed locador, address indexed inquilino, uint256 newEndDate);
    event RentPaymentPending(address indexed inquilino, uint256 dueDate);
    event ContractExpired(address indexed locador, address indexed inquilino);
    event PaymentLate(address indexed inquilino, uint256 daysLate);
    event TimeSimulation(uint256 simulatedTimestamp);

    constructor(
        address _inquilino,
        uint256 _rentAmount,
        uint256 _deposit,
        uint256 _startTimestamp,
        uint256 _endTimestamp // Receber diretamente o timestamp
    ) {
        locador = msg.sender;
        inquilino = _inquilino;
        rentAmount = _rentAmount;
        deposit = _deposit;
        startTimestamp = _startTimestamp;
        endTimestamp = _endTimestamp;
        duracaoContratoSegundos = _endTimestamp - _startTimestamp;
        isTerminated = false;
    }

    function payRent() public payable {
        require(msg.sender == inquilino, unicode"Apenas o inquilino pode pagar o aluguel.");
        require(msg.value == rentAmount, unicode"Valor do aluguel incorreto.");  // Comparação em Wei
        require(!isTerminated, unicode"O contrato foi encerrado.");
        require(isFullySigned(), unicode"O contrato precisa ser assinado por ambas as partes antes de realizar pagamentos.");

        payable(locador).transfer(msg.value);
        emit RentPaid(msg.sender, msg.value);
    }

    function payDeposit() public payable {
        require(msg.sender == inquilino, unicode"Apenas o inquilino pode pagar o deposito.");
        require(msg.value == deposit, unicode"Valor do deposito incorreto.");  // Comparação em Wei
        require(!isTerminated, unicode"O contrato foi encerrado.");
        require(isFullySigned(), unicode"O contrato precisa ser assinado por ambas as partes antes de realizar pagamentos.");
        
        payable(locador).transfer(msg.value);
        emit DepositPaid(msg.sender, msg.value);
    }

    // Funções para retornar o valor de depósito e aluguel
    function getDepositAmount() public view returns (uint256) {
        return deposit;
    }

    function getRentAmount() public view returns (uint256) {
        return rentAmount;
    }

    function terminateContract() public {
        require(msg.sender == locador, unicode"Apenas o locador pode encerrar o contrato.");
        require(!isTerminated, unicode"O contrato já foi encerrado.");
        
        isTerminated = true;
        emit ContractTerminated(locador, inquilino);
    }

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

        if (isFullySigned()) {
            isActive = true;
        }
    }

    function isFullySigned() public view returns (bool) {
        return locadorSigned && inquilinoSigned;
    }

    function isContractActive() public view returns (bool) {
        return !isTerminated;
    }

    function getContractState() public view returns (
    address, address, uint256, uint256, bool, bool, bool, bool
    ) {
        return (
            locador,
            inquilino,
            rentAmount,
            deposit,
            isTerminated,
            locadorSigned,
            inquilinoSigned,
            isActive
        );
    }

    function configurarDataVencimento(uint256 dias) public {
    require(msg.sender == locador, unicode"Apenas o locador pode configurar a data de vencimento.");
    dataVencimentoAluguel = block.timestamp + (dias * 1 days);
    }

    function verificarPagamento() public {
        if (block.timestamp > dataVencimentoAluguel && !isTerminated) {
            emit RentPaymentPending(inquilino, dataVencimentoAluguel);
        }
    }

    function autoRenew() public {
        require(!isTerminated, "Contrato foi encerrado.");
        require(isActive, unicode"Contrato não está ativo."); // Garantir que está ativo
        require(block.timestamp >= dataTerminoContrato, unicode"Contrato ainda não venceu."); // Garantir que chegou a hora

        uint256 newEndTimestamp = dataTerminoContrato + duracaoContratoSegundos;
        dataTerminoContrato = newEndTimestamp;

        emit ContractRenewed(locador, inquilino, newEndTimestamp);
    }

    function checkAndRenew() public {
        require(block.timestamp >= endTimestamp, unicode"Contrato ainda não venceu.");
        autoRenew();
    }

    function getContractEndDate() public view returns (uint256) {
        return dataTerminoContrato;
    }
}
