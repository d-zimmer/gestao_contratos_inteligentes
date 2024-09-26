// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

contract RentalAgreement {
    address public landlord;
    address public tenant;
    uint256 public rentAmount;
    uint256 public deposit;

    constructor(uint256 _rentAmount, uint256 _deposit) {
        landlord = msg.sender;
        rentAmount = _rentAmount;
        deposit = _deposit;
    }

    function payRent() public payable {
        require(msg.value == rentAmount, "Incorrect rent amount");
        payable(landlord).transfer(msg.value);
    }

    function payDeposit() public payable {
        require(msg.value == deposit, "Incorrect deposit amount");
        payable(landlord).transfer(msg.value);
    }
}
