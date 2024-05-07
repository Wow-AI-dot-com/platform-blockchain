# AIxBlock: Decentralized Compute Marketplace

This part implements a decentralized marketplace for computing resources, allowing users to register resources (e.g., GPUs, CPUs), track usage, and handle billing through smart contracts on the EVM-based blockchain.

* Details of design can be found in [docs/SmartContractLogic.md](docs/SmartContractLogic.md)
* List of APIs - tobe updated: [docs/APIs.md](docs/APIs.md)


## Features

* **Resource Registration** : Register computing resources with detailed specifications.
* **Usage Tracking** : Monitor the usage of resources and manage sessions.
* **Dynamic Pricing and Billing** : Implement a pay-as-you-go model for resource usage.

## Prerequisites

* [Node.js](https://nodejs.org/) and npm installed.
* [Truffle](https://www.trufflesuite.com/) or [Hardhat](https://hardhat.org/) for smart contract development and testing.
* [Ganache]() for a local EVM-based blockchain, or testnet/mainnet access through [Infura](https://infura.io/)/[Polygon](polygon).

## Setup

1. Clone the Repository
2. Install Dependencies

## Interact with the Smart Contracts

* **Resource Registration** : Use the `ResourceRegistration` contract to register new computing resources.
  ```javascript
  // Example using ethers.js
  const resourceRegistration = new ethers.Contract(address, abi, signer);
  await resourceRegistration.registerResource(...args);

  ```
* **Start and End Usage Sessions** : Utilize the `UsageTracking` contract to manage resource usage sessions.
  ```javascript
  const usageTracking = new ethers.Contract(address, abi, signer);
  await usageTracking.startSession(resourceId);
  await usageTracking.endSession(sessionId);

  ```
* **Billing and Payments** : Interact with the `Pricing` contract for depositing tokens, withdrawing balances, and automated billing during session ends.
  ```javascript
  const pricing = new ethers.Contract(address, abi, signer);
  await pricing.depositTokens(amount);
  await pricing.withdrawTokens(amount);

  ```
