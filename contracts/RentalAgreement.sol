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
    uint256 public duracaoContratoMeses;

    event RentPaid(address indexed inquilino, uint256 amount);
    event DepositPaid(address indexed inquilino, uint256 amount);
    event ContractTerminated(address indexed locador, address indexed inquilino);
    event AgreementSigned(address signer);
    event ContractRenewed(address indexed locador, address indexed inquilino, uint256 newEndDate);
    event RentPaymentPending(address indexed inquilino, uint256 dueDate);
    event ContractExpired(address indexed locador, address indexed inquilino);
    event PaymentLate(address indexed inquilino, uint256 daysLate);
    event TimeSimulation(uint256 meses);

    constructor(address _inquilino, uint256 _rentAmount, uint256 _deposit, uint256 _duracaoContratoMeses) {
        locador = msg.sender;
        inquilino = _inquilino;
        rentAmount = _rentAmount * (1 ether);
        deposit = _deposit * (1 ether);
        duracaoContratoMeses = _duracaoContratoMeses;  // Armazena a duração do contrato
        isTerminated = false;
        isActive = false;
        dataTerminoContrato = block.timestamp + (duracaoContratoMeses * 30 days);
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

    function verificarStatus() public {
        if (block.timestamp > dataVencimentoAluguel && !isTerminated) {
            uint256 diasAtraso = (block.timestamp - dataVencimentoAluguel) / 1 days;
            emit PaymentLate(inquilino, diasAtraso);
        }
        
        if (block.timestamp > dataTerminoContrato) {
            emit ContractExpired(locador, inquilino);
        }
    }

    function autoRenovar(uint256 durationInMonths) public {
        require(block.timestamp > dataTerminoContrato, unicode"Contrato ainda não expirou.");
        require(!isTerminated, "Contrato foi encerrado.");
        
        uint256 novoPrazo = durationInMonths * 30 days;
        uint256 newStartDate = block.timestamp;
        uint256 newEndDate = newStartDate + novoPrazo;

        dataTerminoContrato = newEndDate;
        
        emit ContractRenewed(locador, inquilino, newEndDate);
    }

    function autoRenew() public {
        require(!isTerminated, "Contrato foi encerrado.");

        if (block.timestamp >= dataTerminoContrato) {
            // Renovar contrato por mais 'duracaoContratoMeses'
            uint256 newEndDate = block.timestamp + (duracaoContratoMeses * 30 days);
            dataTerminoContrato = newEndDate;

            emit ContractRenewed(locador, inquilino, newEndDate);
        }
    }

    function simularPassagemDeMeses(uint256 meses) public {
        require(msg.sender == locador, unicode"Apenas o locador pode simular o tempo.");
        require(meses > 0, unicode"O número de meses deve ser positivo.");

        // Avançar o tempo no contrato (simulado)
        dataTerminoContrato -= meses * 30 days;

        if (block.timestamp >= dataTerminoContrato) {
            autoRenew();
        }

            // Verifique se é necessário renovar o contrato
        if (block.timestamp >= dataTerminoContrato) {
            autoRenew();  // Chama a renovação automática
        }

        emit TimeSimulation(meses);
    }

    function getContractEndDate() public view returns (uint256) {
        return dataTerminoContrato;
    }
}
