// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ResourceRegistration {
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
    }

    Resource[] public resources;
    mapping(uint256 => address) public resourceToOwner; // Maps resource ID to owner address
    uint256 public nextResourceId = 0;

    // Events
    event ResourceRegistered(uint256 indexed resourceId, string resourceType, string provider);
    event ResourceUpdated(uint256 indexed resourceId);
    event ResourceAvailabilityChanged(uint256 indexed resourceId, bool available);

    // Modifier to restrict actions to the resource owner
    modifier onlyResourceOwner(uint256 resourceId) {
        require(resourceToOwner[resourceId] == msg.sender, "Caller is not the resource owner");
        _;
    }

    // Register a new resource
    function registerResource(string memory _resourceType, string memory _provider, uint256 _cpu, uint256 _gpu, uint256 _ram, uint256 _disk, uint256 _pricePerHour) public {
        resources.push(Resource(nextResourceId, _resourceType, _provider, _cpu, _gpu, _ram, _disk, _pricePerHour, true));
        resourceToOwner[nextResourceId] = msg.sender;
        emit ResourceRegistered(nextResourceId, _resourceType, _provider);
        nextResourceId++;
    }

    // Make sure this function is defined and marked as public or external
    function getResourcePricePerHour(uint256 resourceId) external view returns (uint256) {
        require(resourceId < nextResourceId, "Resource does not exist");
        return resources[resourceId].pricePerHour;
    }

    // Update resource details
    function updateResource(uint256 _id, uint256 _cpu, uint256 _gpu, uint256 _ram, uint256 _disk, uint256 _pricePerHour) public onlyResourceOwner(_id) {
        Resource storage resource = resources[_id];
        resource.cpu = _cpu;
        resource.gpu = _gpu;
        resource.ram = _ram;
        resource.disk = _disk;
        resource.pricePerHour = _pricePerHour;
        emit ResourceUpdated(_id);
    }

    // Change the availability of a resource
    function setResourceAvailability(uint256 _id, bool _available) public onlyResourceOwner(_id) {
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
}
