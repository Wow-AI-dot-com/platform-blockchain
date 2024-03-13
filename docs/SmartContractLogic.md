Smart Contract Logic: 


**SC 1: Resource Registration Contract** :

* Handles the registration of compute resources, regardless of whether:

  * provided by your infrastructure,
  * hosted on the user's infrastructure,
  * decentralized marketplace.

**Draft code:**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ResourceRegistration {
    struct Resource {
        uint256 id;
        address provider;
        string resourceType; // "our_infrastructure", "user_hosted", "marketplace"
        uint256 capacity; // VRAM in GB for simplicity
        uint256 vCPU;
        uint256 pricePerHour; // in wei for simplicity
        bool available;
    }

    Resource[] public resources;
    mapping(uint256 => address) public resourceToOwner;
    uint256 public nextResourceId = 0;

    event ResourceRegistered(uint256 indexed resourceId, address indexed provider);
    event ResourceUpdated(uint256 indexed resourceId);
    event ResourceDeregistered(uint256 indexed resourceId);
    event ResourceAvailabilityChanged(uint256 indexed resourceId, bool available);

    // Register a new resource
    function registerResource(string memory _resourceType, uint256 _capacity, uint256 _vCPU, uint256 _pricePerHour) public {
        resources.push(Resource(nextResourceId, msg.sender, _resourceType, _capacity, _vCPU, _pricePerHour, true));
        resourceToOwner[nextResourceId] = msg.sender;
        emit ResourceRegistered(nextResourceId, msg.sender);
        nextResourceId++;
    }

    // Update resource details
    function updateResource(uint256 _resourceId, string memory _resourceType, uint256 _capacity, uint256 _vCPU, uint256 _pricePerHour, bool _available) public {
        require(msg.sender == resourceToOwner[_resourceId], "Caller is not the owner of the resource");
        Resource storage resource = resources[_resourceId];
        resource.resourceType = _resourceType;
        resource.capacity = _capacity;
        resource.vCPU = _vCPU;
        resource.pricePerHour = _pricePerHour;
        resource.available = _available;
        emit ResourceUpdated(_resourceId);
    }

    // Deregister a resource
    function deregisterResource(uint256 _resourceId) public {
        require(msg.sender == resourceToOwner[_resourceId], "Caller is not the owner of the resource");
        delete resourceToOwner[_resourceId];
        delete resources[_resourceId];
        emit ResourceDeregistered(_resourceId);
    }

    // Change the availability of a resource
    function setResourceAvailability(uint256 _resourceId, bool _available) public {
        require(msg.sender == resourceToOwner[_resourceId], "Caller is not the owner of the resource");
        Resource storage resource = resources[_resourceId];
        resource.available = _available;
        emit ResourceAvailabilityChanged(_resourceId, _available);
    }

    // Function to estimate the cost of renting a resource
    function estimateRentCost(uint256 _resourceId, uint256 _hours) public view returns (uint256) {
        require(_resourceId < resources.length, "Resource ID is out of bounds");
        require(_hours > 0, "Rental period must be greater than 0");
    
        Resource memory resource = resources[_resourceId];
        require(resource.available, "Resource is not available");

        uint256 rentCost = resource.pricePerHour * _hours;
        return rentCost;
    }


    // Helper function to get total number of resources registered
    function getTotalResources() public view returns (uint256) {
        return resources.length;
    }

    // Helper function to get a specific resource by id
    function getResourceById(uint256 _resourceId) public view returns (Resource memory) {
        require(_resourceId < resources.length, "Resource ID is out of bounds");
	return resources[_resourceId];
	}
}



```
