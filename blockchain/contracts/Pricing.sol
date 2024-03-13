// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./ResourceRegistration.sol";


contract Pricing is Ownable, ReentrancyGuard {
    IERC20 public axbToken;
    ResourceRegistration public resourceRegistration;

    mapping(address => uint256) public userBalances;

    event PaymentProcessed(address indexed user, uint256 amount, uint256 resourceId);
    event UserBalanceUpdated(address indexed user, uint256 newBalance);

    constructor(address _axbTokenAddress, address _resourceRegistrationAddress)
        Ownable(msg.sender) {
        axbToken = IERC20(_axbTokenAddress);
        resourceRegistration = ResourceRegistration(_resourceRegistrationAddress);
    }

    // Function for users to deposit AXB tokens into their balance within the contract
    function depositTokens(uint256 amount) external nonReentrant {
        require(axbToken.transferFrom(msg.sender, address(this), amount), "Transfer failed");
        userBalances[msg.sender] += amount;
        emit UserBalanceUpdated(msg.sender, userBalances[msg.sender]);
    }

    // Users can withdraw their unused AXB tokens
    function withdrawTokens(uint256 amount) external nonReentrant {
        require(userBalances[msg.sender] >= amount, "Insufficient balance");
        userBalances[msg.sender] -= amount;
        require(axbToken.transfer(msg.sender, amount), "Transfer failed");
        emit UserBalanceUpdated(msg.sender, userBalances[msg.sender]);
    }

    // Called by the UsageTracking contract to process payment for a resource usage session
    function processPayment(address user, uint256 resourceId, uint256 durationInSeconds) external nonReentrant {
        uint256 pricePerHour = resourceRegistration.getResourcePricePerHour(resourceId);
        uint256 cost = calculateCost(pricePerHour, durationInSeconds);

        require(userBalances[user] >= cost, "Insufficient balance for payment");
        userBalances[user] -= cost;
        emit PaymentProcessed(user, cost, resourceId);
    }

    // Helper function to calculate the cost based on usage duration and price per hour
    function calculateCost(uint256 pricePerHour, uint256 durationInSeconds) public pure returns (uint256) {
        return pricePerHour * durationInSeconds / 3600;
    }

    // Additional helper functions for balance inquiries, etc.
}
