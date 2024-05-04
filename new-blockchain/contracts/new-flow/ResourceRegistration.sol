// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ResourceRegistration {
    // Add a new field to the Resource struct for maximum concurrent sessions
    struct Resource {
        uint256 id;
        string resourceType; // LabelingTool, Storage, MLNotebook, MLTraining
        string provider; // e.g., "Intel"
        uint256 cpu; // Number of CPUs for the resource
        uint256 gpu; // Number of GPUs for the resource
        uint256 ram; // Amount of RAM in GB
        uint256 disk; // Disk space in GB
        uint256 pricePerHour; // Price per hour in tokens
        bool available; // Availability of the resource
        uint256 maxConcurrentSessions; // NEW: Max number of concurrent sessions
        bool underVerification; // Indicates whether the resource is under verification due to a report
    }

    Resource[] public resources;
    mapping(address => uint256[]) public ownerResourceList; // Maps resource ID to owner address
    mapping(uint256 => address) public resourceToOwner; // Maps resource ID to owner address
    mapping(uint256 => bool) public reportedResources; // Tracks resources that have been reported for review
    uint256 public nextResourceId = 0;

    // Events
    event ResourceRegistered(
        uint256 indexed resourceId,
        string resourceType,
        string provider
    );
    event ResourceUpdated(uint256 indexed resourceId);
    event ResourceAvailabilityChanged(
        uint256 indexed resourceId,
        bool available
    );
    event ResourceReported(uint256 indexed resourceId, address reporter);
    event ResourceVerificationStatusChanged(
        uint256 indexed resourceId,
        bool underVerification
    );

    // Modifier to restrict actions to the resource owner
    modifier onlyResourceOwner(uint256 resourceId) {
        require(
            resourceToOwner[resourceId] == msg.sender,
            "Caller is not the resource owner"
        );
        _;
    }

    // Register a new resource
    // Register a new resource
    function registerResource(
        string memory _resourceType,
        string memory _provider,
        uint256 _cpu,
        uint256 _gpu,
        uint256 _ram,
        uint256 _disk,
        uint256 _pricePerHour,
        uint256 _maxConcurrentSessions
    ) public {
        resources.push(
            Resource({
                id: nextResourceId,
                resourceType: _resourceType,
                provider: _provider,
                cpu: _cpu,
                gpu: _gpu,
                ram: _ram,
                disk: _disk,
                pricePerHour: _pricePerHour,
                available: true,
                maxConcurrentSessions: _maxConcurrentSessions,
                underVerification: false // Initially, resources are not under verification
            })
        );
        resourceToOwner[nextResourceId] = msg.sender;
        ownerResourceList[msg.sender].push(nextResourceId);
        emit ResourceRegistered(nextResourceId, _resourceType, _provider);
        nextResourceId++;
    }

    function registerMultiResources(
        string[] memory _resourceTypes,
        string[] memory _providers,
        uint256[] memory _cpus,
        uint256[] memory _gpus,
        uint256[] memory _rams,
        uint256[] memory _disks,
        uint256[] memory _pricesPerHour,
        uint256[] memory _maxConcurrentSessions
    ) public {
        require(
            _resourceTypes.length == _providers.length &&
                _providers.length == _cpus.length &&
                _cpus.length == _gpus.length &&
                _gpus.length == _rams.length &&
                _rams.length == _disks.length &&
                _disks.length == _pricesPerHour.length &&
                _pricesPerHour.length == _maxConcurrentSessions.length,
            "All input arrays must have the same length"
        );

        for (uint i = 0; i < _resourceTypes.length; i++) {
            resources.push(
                Resource({
                    id: nextResourceId,
                    resourceType: _resourceTypes[i],
                    provider: _providers[i],
                    cpu: _cpus[i],
                    gpu: _gpus[i],
                    ram: _rams[i],
                    disk: _disks[i],
                    pricePerHour: _pricesPerHour[i],
                    available: true,
                    maxConcurrentSessions: _maxConcurrentSessions[i],
                    underVerification: false // Initially, resources are not under verification
                })
            );
            resourceToOwner[nextResourceId] = msg.sender;
            ownerResourceList[msg.sender].push(nextResourceId);

            emit ResourceRegistered(
                nextResourceId,
                _resourceTypes[i],
                _providers[i]
            );
            nextResourceId++;
        }
    }

    // Function to update the verification status of a resource, callable by the contract owner or a designated verifier
    function setResourceVerificationStatus(
        uint256 _resourceId,
        bool _underVerification
    ) public {
        require(_resourceId < nextResourceId, "Resource does not exist");
        require(reportedResources[_resourceId], "Resource not reported");

        resources[_resourceId].underVerification = _underVerification;
        if (!_underVerification) {
            // If resource verification is complete and the resource is cleared, reset its reported status
            reportedResources[_resourceId] = false;
        }

        emit ResourceVerificationStatusChanged(_resourceId, _underVerification);
    }

    // Function to report a resource for verification
    function reportResource(uint256 _resourceId) public {
        require(_resourceId < nextResourceId, "Resource does not exist");
        require(!reportedResources[_resourceId], "Resource already reported");
        reportedResources[_resourceId] = true;
        resources[_resourceId].underVerification = true;

        emit ResourceReported(_resourceId, msg.sender);
    }

    // Make sure this function is defined and marked as public or external
    function getResourcePricePerHour(
        uint256 resourceId
    ) external view returns (uint256) {
        require(resourceId < nextResourceId, "Resource does not exist");
        return resources[resourceId].pricePerHour;
    }

    // Update resource details
    function updateResource(
        uint256 _id,
        uint256 _cpu,
        uint256 _gpu,
        uint256 _ram,
        uint256 _disk,
        uint256 _pricePerHour
    ) public onlyResourceOwner(_id) {
        Resource storage resource = resources[_id];
        resource.cpu = _cpu;
        resource.gpu = _gpu;
        resource.ram = _ram;
        resource.disk = _disk;
        resource.pricePerHour = _pricePerHour;
        emit ResourceUpdated(_id);
    }

    // Change the availability of a resource
    function setResourceAvailability(
        uint256 _id,
        bool _available
    ) public onlyResourceOwner(_id) {
        Resource storage resource = resources[_id];
        resource.available = _available;
        emit ResourceAvailabilityChanged(_id, _available);
    }

    // Get details of a resource
    function getResource(uint256 _id) public view returns (Resource memory) {
        require(_id < nextResourceId, "Resource does not exist");
        return resources[_id];
    }

    // Get total number of resources
    function getTotalResources() public view returns (uint256) {
        return nextResourceId;
    }

    // Get resources of address
    function getResourceByAddress(
        address _owner
    ) public view returns (uint256[] memory) {
        return ownerResourceList[_owner];
    }
}
