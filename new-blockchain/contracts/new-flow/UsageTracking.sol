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
        uint256 totalDeposit;
        bool autoRental;
    }

    mapping(uint256 => UsageSession) public sessions; // Maps session IDs to UsageSessions
    mapping(uint256 => uint256) public activeSessionsCount; // Maps resource IDs to count of active sessions
    mapping(address => uint256[]) public userActiveSessionList; // Maps resource IDs to count of active sessions
    uint256 public nextSessionId = 0;

    event SessionStarted(
        uint256 indexed sessionId,
        uint256 indexed resourceId,
        uint256 depositAmount,
        address user,
        bool autoRental
    );
    event SessionEnded(
        uint256 indexed sessionId,
        uint256 indexed resourceId,
        address user
    );

    constructor(address _resourceRegistrationAddress, address _pricingAddress) {
        resourceRegistration = ResourceRegistration(
            _resourceRegistrationAddress
        );
        pricingContract = Pricing(_pricingAddress);
    }

    function startSession(
        uint256 _resourceId,
        uint256 _totalHoursEstimate
    ) external {
        ResourceRegistration.Resource memory resource = resourceRegistration
            .getResource(_resourceId);
        require(resource.available, "Resource not available");
        uint256 totalDeposit = pricingContract.calculateForDeposit(
            resource.pricePerHour,
            _totalHoursEstimate,
            msg.sender
        );

        sessions[nextSessionId] = UsageSession({
            resourceId: _resourceId,
            user: msg.sender,
            startTime: block.timestamp,
            endTime: 0, // Indicates the session is currently active
            totalDeposit: totalDeposit,
            autoRental: false
        });
        userActiveSessionList[msg.sender].push(nextSessionId);

        activeSessionsCount[_resourceId]++; // Increment the count of active sessions for this resource
        emit SessionStarted(
            nextSessionId,
            _resourceId,
            totalDeposit,
            msg.sender,
            false
        );
        nextSessionId++;
    }

    function startSessionAutoRental() external {
        uint256 totalDeposit = pricingContract.calculateForDepositForAutoRental(
            msg.sender
        );

        sessions[nextSessionId] = UsageSession({
            resourceId: 0,
            user: msg.sender,
            startTime: block.timestamp,
            endTime: 0, // Indicates the session is currently active
            totalDeposit: totalDeposit,
            autoRental: true
        });
        userActiveSessionList[msg.sender].push(nextSessionId);

        activeSessionsCount[0]++; // Increment the count of active sessions for this resource
        emit SessionStarted(nextSessionId, 0, totalDeposit, msg.sender, true);
        nextSessionId++;
    }

    function startMultiSessions(
        uint256[] memory _resourceIds,
        uint256[] memory _totalHoursEstimate
    ) external {
        require(
            _resourceIds.length == _totalHoursEstimate.length,
            "Invalid input"
        );
        for (uint i = 0; i < _resourceIds.length; i++) {
            uint256 _resourceId = _resourceIds[i];
            ResourceRegistration.Resource memory resource = resourceRegistration
                .getResource(_resourceId);
            require(resource.available, "Resource not available");
            uint256 totalDeposit = pricingContract.calculateForDeposit(
                resource.pricePerHour,
                _totalHoursEstimate[i],
                msg.sender
            );

            sessions[nextSessionId] = UsageSession({
                resourceId: _resourceIds[i],
                user: msg.sender,
                startTime: block.timestamp,
                endTime: 0, // Indicates the session is currently active
                totalDeposit: totalDeposit,
                autoRental: false
            });
            userActiveSessionList[msg.sender].push(nextSessionId);

            activeSessionsCount[_resourceId]++; // Increment the count of active sessions for this resource
            emit SessionStarted(
                nextSessionId,
                _resourceId,
                totalDeposit,
                msg.sender,
                false
            );
            nextSessionId++;
        }
    }

    function endSession(uint256 _sessionId) external {
        UsageSession storage session = sessions[_sessionId];
        address _provider = resourceRegistration.resourceToOwner(
            session.resourceId
        );

        require(
            msg.sender == session.user,
            "Only the session initiator can end it"
        );
        require(session.endTime == 0, "Session already ended");

        session.endTime = block.timestamp;
        activeSessionsCount[session.resourceId]--; // Decrement the count of active sessions for this resource
        uint256[] storage userSessions = userActiveSessionList[msg.sender];
        for (uint i = 0; i < userSessions.length; i++) {
            if (userSessions[i] == _sessionId) {
                userSessions[i] = userSessions[userSessions.length - 1];
                userSessions.pop();
                break;
            }
        }

        emit SessionEnded(_sessionId, session.resourceId, msg.sender);

        // Calculate the session duration in seconds
        uint256 duration = session.endTime - session.startTime;
        // Notify the Pricing contract to calculate and deduct cost
        pricingContract.processPayment(
            session.user,
            _provider,
            session.resourceId,
            duration,
            session.totalDeposit
        );
    }

    function endMultiSessions(uint256[] memory _sessionIds) external {
        for (uint i = 0; i < _sessionIds.length; i++) {
            uint256 _sessionId = _sessionIds[i];
            UsageSession storage session = sessions[_sessionId];
            address _provider = resourceRegistration.resourceToOwner(
                session.resourceId
            );

            require(
                msg.sender == session.user,
                "Only the session initiator can end it"
            );
            require(session.endTime == 0, "Session already ended");

            session.endTime = block.timestamp;
            activeSessionsCount[session.resourceId]--; // Decrement the count of active sessions for this resource

            emit SessionEnded(_sessionId, session.resourceId, msg.sender);

            // Calculate the session duration in seconds
            uint256 duration = session.endTime - session.startTime;
            // Notify the Pricing contract to calculate and deduct cost
            pricingContract.processPayment(
                session.user,
                _provider,
                session.resourceId,
                duration,
                session.totalDeposit
            );
        }
    }

    // Helper function to get the number of active sessions for a specific resource
    function getActiveSessionsCount(
        uint256 _resourceId
    ) external view returns (uint256) {
        return activeSessionsCount[_resourceId];
    }

    // Get sessions of address
    function getActiveSessionByAddress(
        address _user
    ) public view returns (uint256[] memory) {
        return userActiveSessionList[_user];
    }

    // Get sessions data
    function getSession(
        uint256 _index
    ) public view returns (UsageSession memory) {
        return sessions[_index];
    }
}
