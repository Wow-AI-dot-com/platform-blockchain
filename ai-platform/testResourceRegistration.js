const express = require('express');
const Web3 = require('web3');
const fs = require('fs');

const app = express();
const port = 3000;

app.use(express.json());

const web3 = new Web3('http://localhost:8545');

const contractABI = JSON.parse(fs.readFileSync('blockchain/build/contracts/ResourceRegistration.json', 'utf-8')).abi;
const contractAddress = '0xd9145CCE52D386f254917e481eB44e9943F39138';
const contract = new web3.eth.Contract(contractABI, contractAddress);

app.post('/registerResource', async(req, res) => {
    const { resourceType, capacity, vCPU, pricePerHour } = req.body;
    const account = '0xYourAccountAddress'; // The Ethereum address to interact with the contract
    const privateKey = '0xYourPrivateKey'; // The private key corresponding to the account

    const transaction = contract.methods.registerResource(resourceType, capacity, vCPU, pricePerHour);

    const options = {
        to: transaction._parent._address,
        data: transaction.encodeABI(),
        gas: await transaction.estimateGas({ from: account }),
        gasPrice: await web3.eth.getGasPrice() // or specify your own gas price
    };

    try {
        const signed = await web3.eth.accounts.signTransaction(options, privateKey);
        const receipt = await web3.eth.sendSignedTransaction(signed.rawTransaction);
        res.json({ success: true, transactionHash: receipt.transactionHash });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

app.listen(port, () => {
    console.log(`API server listening at http://localhost:${port}`);
});