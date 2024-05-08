# Smart Contract Logic:

The Decentralized Compute MarketPlace include some of smart contracts:

* AXBToken.sol
* ResourceRegistration.sol
* Pricing.sol
* UsageTracking.sol

# **AXBToken.sol** for testing:

```solidity

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract AXBToken is ERC20 {
    constructor(
        string memory name,
        string memory symbol,
        uint256 initialSupply
    ) ERC20(name, symbol){
        _mint(msg.sender, initialSupply);
    }
}

```

# **SC 1: Resource Registration Contract** :

* Handles the registration of compute resources
* List functions:

### Write function
1. registerResource: Register single resource
```
function registerResource(
        string memory _resourceType, //e.g., LabelingTool, Storage, MLNotebook, MLTraining
        string memory _provider,  //e.g., "Intel" 
        uint256 _cpu, // Number of CPUs for the resource
        uint256 _gpu, // Number of GPUs for the resource
        uint256 _ram, // Amount of RAM in GB
        uint256 _disk, // Disk space in GB
        uint256 _pricePerHour // Price per hour in tokens(wei)
    )
```

2. registerMultiResources: Register multi resources
```
function registerResource(
        string[] memory _resourceTypes, //e.g., LabelingTool, Storage, MLNotebook, MLTraining
        string[] memory _providers,  //e.g., "Intel" 
        uint256[] memory _cpus, // Array number of CPUs for the resource
        uint256[] memory _gpus, // Array number of GPUs for the resource
        uint256[] memory _rams, // Array amount of RAM in GB
        uint256[] memory _disks, // Array disk space in GB
        uint256[] memory _pricesPerHour // Array price per hour in tokens(wei)
    )
```

3. updateResource: Update resource info, only can call by the owner of the resource
```
function updateResource(
        uint256 _id, // resource 's id
        uint256 _cpu,
        uint256 _gpu,
        uint256 _ram,
        uint256 _disk,
        uint256 _pricePerHour
    ) public onlyResourceOwner(_id)
```

### Read function

1. getResource: Get resource info by resource's id
```
 function getResource(uint256 _id)
```
**Response**
```
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
        bool underVerification; // Indicates whether the resource is under verification due to a report
    }
```

2. getTotalResources: Get total registered resources

```
 function getTotalResources()
```

**Response**: Number of registered resources

3. getResourceByAddress: Get resources's id of a specific address

```
function getResourceByAddress(
        address _owner
    )
```
**Response**: Array id resources of an address
  

# **Smart Contract 2: Pricing.sol**
* Handles deposit and withdraw of users
### Write function
1. depositTokens: Deposit an amount of token to rent resource
```
function depositTokens(
        uint256 amount
    )
```

2. withdrawTokens: Withdraw an amount of token to user wallet
```
function withdrawTokens(
        uint256 amount
    )
```
### Read function

1. getUserBalance: Get balance of a wallet address
```
function getUserBalance(
        address _user
    )
```

**Response**: User balance


# Smart Contract 3: UsageTracking.sol

### Write function
1. startSession: User start a session with 1 resource

**Require**: 
* User has enough balance to start a session 
    * user balance >= totalHoursEstimate * resourcePricePerHour 
```
function startSession(
        uint256 _resourceId,
        uint256 _totalHoursEstimate
    ) 
```

2. startMultiSessions: User start multi session with multi resource

**Require**: 

* User has enough balance to start a session 
    * user balance >= (totalHoursEstimate[0] * resourcePricePerHour[0] + totalHoursEstimate[1] * resourcePricePerHour[1] + ... + totalHoursEstimate[n] * resourcePricePerHour[n]) 

```
function startMultiSessions(
        uint256[] memory _resourceIds,
        uint256[] memory _totalHoursEstimate
    )
```

3. startSessionAutoRental: User start session with auto rental

**Require**: 

* User has enough balance > 50 token

```
function startSessionAutoRental()
```

4. endSession: End a session

**Require**: 
* Only owner of session can end session 

```
function endSession(
        uint256 _sessionId
    ) 
```

5. endMultiSessions: User end multi session

**Require**: 

* Only owner of session can end session 

```
function endMultiSessions(
        uint256[] memory _sessionIds
    )
```


### Read function

1. getSession: Get session info
```
 function getSession(uint256 _id)
```
**Response**
```
struct UsageSession {
        uint256 resourceId;
        address user;
        uint256 startTime;
        uint256 endTime;
        uint256 totalDeposit;
        bool autoRental;
    }
```

2. getActiveSessionsCount: Get active sessions for a specific resource

```
 function getActiveSessionsCount(
    uint256 _resourceId
 )
```

**Response**: Number of active sessions for a specific resource

3. getActiveSessionByAddress: Get session's ids of a specific address

```
function getActiveSessionByAddress(
        address _user
    )
```
**Response**: Array ids sessions of an address
  