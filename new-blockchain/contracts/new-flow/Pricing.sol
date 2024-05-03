// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./ResourceRegistration.sol";

contract Pricing is Ownable, ReentrancyGuard {
    IERC20 public token;
    ResourceRegistration public resourceRegistration;

    uint256 public constant HOUR_IN_SECOND = 3600;
    uint256 public autoRentalPrice = 50;

    mapping(address => uint256) public userBalances;

    mapping(address => uint256) public userDeposit;

    event PaymentProcessed(
        address indexed user,
        uint256 amount,
        uint256 resourceId
    );

    event UserBalanceUpdated(address indexed user, uint256 newBalance);

    event AutoRentalPriceUpdated(uint256 newBalance);

    constructor(
        address _tokenAddress,
        address _resourceRegistrationAddress
    ) Ownable() {
        token = IERC20(_tokenAddress);
        resourceRegistration = ResourceRegistration(
            _resourceRegistrationAddress
        );
    }

    modifier onlyResourceRegistration() {
        require(
            msg.sender == address(resourceRegistration),
            "Only the resource registration contract can call this function"
        );
        _;
    }

    // Function for users to deposit AXB tokens into their balance within the contract
    function depositTokens(uint256 amount) external nonReentrant {
        require(
            token.transferFrom(msg.sender, address(this), amount),
            "Transfer failed"
        );
        userBalances[msg.sender] += amount;
        emit UserBalanceUpdated(msg.sender, userBalances[msg.sender]);
    }

    // Users can withdraw their unused AXB tokens
    function withdrawTokens(uint256 amount) external nonReentrant {
        require(userBalances[msg.sender] >= amount, "Insufficient balance");
        userBalances[msg.sender] -= amount;
        require(token.transfer(msg.sender, amount), "Transfer failed");
        emit UserBalanceUpdated(msg.sender, userBalances[msg.sender]);
    }

    // Called by the UsageTracking contract to process payment for a resource usage session
    function processPayment(
        address user,
        address provider,
        uint256 resourceId,
        uint256 durationInSeconds,
        uint256 totalDeposit
    ) external nonReentrant onlyResourceRegistration {
        uint256 pricePerHour = resourceRegistration.getResourcePricePerHour(
            resourceId
        );
        uint256 cost = calculateCost(pricePerHour, durationInSeconds);
        uint256 refund = totalDeposit - cost;

        require(userBalances[user] >= cost, "Insufficient balance for payment");
        userBalances[user] += refund;
        userBalances[provider] += cost;
        userDeposit[user] -= totalDeposit;

        emit PaymentProcessed(user, cost, resourceId);
    }

    // Helper function to calculate the cost based on usage duration and price per hour
    function calculateCost(
        uint256 pricePerHour,
        uint256 durationInSeconds
    ) public pure returns (uint256) {
        return (pricePerHour * durationInSeconds) / HOUR_IN_SECOND;
    }

    // Additional helper functions for balance inquiries, etc.

    function calculateForDeposit(
        uint256 _pricePerHour,
        uint256 _durationInHours,
        address _user
    ) public onlyResourceRegistration returns (uint256) {
        require(
            _pricePerHour > 0 && _durationInHours > 0,
            "Invalid price or duration"
        );
        uint256 _totalCost = _pricePerHour * _durationInHours;
        require(_totalCost <= userBalances[_user], "Insufficient balance");
        userBalances[_user] -= _totalCost;
        userDeposit[_user] += _totalCost;

        return _totalCost;
    }

    function calculateForDepositForAutoRental(
        address _user
    ) public onlyResourceRegistration returns (uint256) {
        require(userBalances[_user] > autoRentalPrice, "Invalid balance");
        userBalances[_user] -= autoRentalPrice;
        userDeposit[_user] += autoRentalPrice;

        return autoRentalPrice;
    }

    // Change auto rental price
    function newAutoRentalPrice(uint256 amount) external onlyOwner {
        require(amount > 0, "Invalid price");
        autoRentalPrice = amount;
        emit AutoRentalPriceUpdated(autoRentalPrice);
    }
}
