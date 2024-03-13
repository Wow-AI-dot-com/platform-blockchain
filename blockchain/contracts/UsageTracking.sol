// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./ResourceRegistration.sol";
import "./Pricing.sol";

contract UsageTracking {
    ResourceRegistration public resourceRegistration;
    Pricing public pricingContract;

    struct UsageSession {
        uint256 resourceId;
        address user;
        uint256 startTime;
        uint256 endTime;
    }

    mapping(uint256 => UsageSession) public sessions;
    uint256 public nextSessionId = 0;

    event SessionStarted(uint256 indexed sessionId, uint256 indexed resourceId, address user);
    event SessionEnded(uint256 indexed sessionId, uint256 indexed resourceId, address user);

    constructor(address _resourceRegistrationAddress, address _pricingAddress) {
        resourceRegistration = ResourceRegistration(_resourceRegistrationAddress);
        pricingContract = Pricing(_pricingAddress);
    }

    function startSession(uint256 _resourceId) external {
        require(resourceRegistration.isResourceAvailable(_resourceId), "Resource not available");
        
        sessions[nextSessionId] = UsageSession({
            resourceId: _resourceId,
            user: msg.sender,
            startTime: block.timestamp,
            endTime: 0
        });
        
        emit SessionStarted(nextSessionId, _resourceId, msg.sender);
        nextSessionId++;
    }

    function endSession(uint256 _sessionId) external {
        UsageSession storage session = sessions[_sessionId];
        require(msg.sender == session.user, "Only the session initiator can end it");
        require(session.endTime == 0, "Session already ended");

        session.endTime = block.timestamp;
        
        emit SessionEnded(_sessionId, session.resourceId, msg.sender);

        // Notify the Pricing contract to calculate and deduct cost
        uint256 duration = session.endTime - session.startTime;
        pricingContract.calculateCost(session.resourceId, session.user, duration);
    }
}
