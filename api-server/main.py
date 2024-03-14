from fastapi import FastAPI, HTTPException
from web3 import Web3
import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

# Setup Web3 connection
w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))
w3.middleware_onion.inject(Web3.middleware.geth_poa_middleware, layer=0)

# Ensure you replace 'path/to/ABI.json' with the actual path to your ABI files
with open("blockchain/build/contracts/ResourceRegistration.json") as f:
    resource_registration_abi = json.load(f)
resource_registration_address = os.getenv("RESOURCE_REGISTRATION_ADDRESS")
resource_registration = w3.eth.contract(address=resource_registration_address, abi=resource_registration_abi)

with open("blockchain/build/contracts/PricingABI.json") as f:
    pricing_abi = json.load(f)
pricing_address = os.getenv("PRICING_ADDRESS")
pricing = w3.eth.contract(address=pricing_address, abi=pricing_abi)

with open("blockchain/build/contracts/UsageTrackingABI.json") as f:
    usage_tracking_abi = json.load(f)
usage_tracking_address = os.getenv("USAGE_TRACKING_ADDRESS")
usage_tracking = w3.eth.contract(address=usage_tracking_address, abi=usage_tracking_abi)

# Assume an unlocked account or use a wallet management solution
w3.eth.default_account = w3.eth.accounts[0]

# Input models for our endpoints
class ResourceRegistrationModel(BaseModel):
    resourceType: str
    provider: str
    cpu: int
    gpu: int
    ram: int
    disk: int
    price_per_hour: float
    max_concurrent_sessions: int

class DepositTokensModel(BaseModel):
    amount: float

class StartSessionModel(BaseModel):
    resourceId: int

class EndSessionModel(BaseModel):
    sessionId: int

class WithdrawTokensModel(BaseModel):
    amount: float

class ReportResourceModel(BaseModel):
    resourceId: int

class ResourceAvailabilityModel(BaseModel):
    resourceId: int
    available: bool

class VerificationStatusModel(BaseModel):
    resourceId: int
    underVerification: bool


# ResourceRegistration endpoint
@app.post("/register_resource/")
def register_resource(resource: ResourceRegistrationModel):
    tx_hash = resource_registration.functions.registerResource(
        resource.resourceType,
        resource.provider,
        resource.cpu,
        resource.gpu,
        resource.ram,
        resource.disk,
        Web3.toWei(resource.price_per_hour, 'ether'),
        resource.max_concurrent_sessions
    ).transact()
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return {"transaction_receipt": receipt.transactionHash.hex()}

# Pricing endpoints
@app.post("/deposit_tokens/")
def deposit_tokens(deposit: DepositTokensModel):
    tx_hash = pricing.functions.depositTokens(
        Web3.toWei(deposit.amount, 'ether')
    ).transact()
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return {"transaction_receipt": receipt.transactionHash.hex()}

# UsageTracking endpoints
@app.post("/start_session/")
def start_session(session: StartSessionModel):
    tx_hash = usage_tracking.functions.startSession(session.resourceId).transact()
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return {"transaction_receipt": receipt.transactionHash.hex()}

@app.post("/end_session/")
def end_session(session: EndSessionModel):
    tx_hash = usage_tracking.functions.endSession(session.sessionId).transact()
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return {"transaction_receipt": receipt.transactionHash.hex()}


@app.post("/withdraw_tokens/")
def withdraw_tokens(data: WithdrawTokensModel):
    #  the `withdrawTokens` function exists in the Pricing contract
    tx = pricing.functions.withdrawTokens(
        Web3.toWei(data.amount, 'ether')
    ).buildTransaction({'from': default_account.address, 'nonce': w3.eth.getTransactionCount(default_account.address)})
    signed_tx = default_account.sign_transaction(tx)
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    return {"transaction_hash": tx_hash.hex()}

@app.post("/report_resource/")
def report_resource(data: ReportResourceModel):
    #  the `reportResource` function exists in ResourceRegistration contract
    tx = resource_registration.functions.reportResource(
        data.resourceId
    ).buildTransaction({'from': default_account.address, 'nonce': w3.eth.getTransactionCount(default_account.address)})
    signed_tx = default_account.sign_transaction(tx)
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    return {"transaction_hash": tx_hash.hex()}

@app.post("/set_resource_availability/")
def set_resource_availability(data: ResourceAvailabilityModel):
    #  the `setResourceAvailability` function exists in your ResourceRegistration contract
    tx = resource_registration.functions.setResourceAvailability(
        data.resourceId, data.available
    ).buildTransaction({'from': default_account.address, 'nonce': w3.eth.getTransactionCount(default_account.address)})
    signed_tx = default_account.sign_transaction(tx)
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    return {"transaction_hash": tx_hash.hex()}

@app.post("/update_verification_status/")
def update_verification_status(data: VerificationStatusModel):
    #  an updateVerificationStatus method in  smart contract to update resource verification
    tx = resource_registration.functions.setResourceVerificationStatus(
        data.resourceId, data.underVerification
    ).buildTransaction({
        'from': default_account.address,
        'nonce': w3.eth.getTransactionCount(default_account.address)
    })
    signed_tx = default_account.sign_transaction(tx)
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    return {"transaction_hash": tx_hash.hex()}

