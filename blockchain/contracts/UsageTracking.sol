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

    mapping(uint256 => UsageSession) public sessions; // Maps session IDs to UsageSessions
    mapping(uint256 => uint256) public activeSessionsCount; // Maps resource IDs to count of active sessions
    uint256 public nextSessionId = 0;

    event SessionStarted(uint256 indexed sessionId, uint256 indexed resourceId, address user);
    event SessionEnded(uint256 indexed sessionId, uint256 indexed resourceId, address user);

    constructor(address _resourceRegistrationAddress, address _pricingAddress) {
        resourceRegistration = ResourceRegistration(_resourceRegistrationAddress);
        pricingContract = Pricing(_pricingAddress);
    }

    function startSession(uint256 _resourceId) external {
        ResourceRegistration.Resource memory resource = resourceRegistration.getResource(_resourceId);
        require(resource.available, "Resource not available");
        require(activeSessionsCount[_resourceId] < resource.maxConcurrentSessions, "Resource at full capacity");

        sessions[nextSessionId] = UsageSession({
            resourceId: _resourceId,
            user: msg.sender,
            startTime: block.timestamp,
            endTime: 0 // Indicates the session is currently active
        });

        activeSessionsCount[_resourceId]++; // Increment the count of active sessions for this resource
        emit SessionStarted(nextSessionId, _resourceId, msg.sender);
        nextSessionId++;
    }

    function endSession(uint256 _sessionId) external {
        UsageSession storage session = sessions[_sessionId];
        require(msg.sender == session.user, "Only the session initiator can end it");
        require(session.endTime == 0, "Session already ended");

        session.endTime = block.timestamp;
        activeSessionsCount[session.resourceId]--; // Decrement the count of active sessions for this resource
        
        emit SessionEnded(_sessionId, session.resourceId, msg.sender);

        // Calculate the session duration in seconds
        uint256 duration = session.endTime - session.startTime;
        // Notify the Pricing contract to calculate and deduct cost
        pricingContract.processPayment(session.user, session.resourceId, duration);
    }

    // Helper function to get the number of active sessions for a specific resource
    function getActiveSessionsCount(uint256 _resourceId) external view returns (uint256) {
        return activeSessionsCount[_resourceId];
    }
}
