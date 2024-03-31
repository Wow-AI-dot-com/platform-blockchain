from fastapi import FastAPI, HTTPException, Header
from web3 import Web3
import os
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
import secrets
from eth_account import Account
from model import Wallet  # assuming you have a Pydantic model named Item
from service import create_item, create_item_if_not_exist, get_one_by_user_id, register_rent, encrypt_private_key, decrypt_private_key, end_rent, error_resource, withdraw_token_on_ramp, worker, withdraw_token_off_ramp , get_transfer_off_ramp_by_status, update_status, get_one_transfer_off_ramp_request, get_token_price, get_all_token # assuming you have a Pydantic model named Item
from bson import ObjectId
import aioredis
import asyncio
import pickle
from web3.middleware import geth_poa_middleware
from typing import List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from utils import marketplace_abi, token_abi, TransferStatus, pancake_abi
import threading
from decimal import Decimal
import base64
import json
import queue
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time

load_dotenv()
global app
app = FastAPI()

# Setup Web3 connection
app.w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))
private_key = os.getenv("PRIVATE_KEY")
app.account = Account.from_key(private_key)

assert app.w3.is_connected()
contract_address = os.getenv("MARKETPLACE_CONTRACT_ADDRESS")  # replace with your contract address
token_address = os.getenv("TOKEN_CONTRACT_ADDRESS")  # replace with your contract address
pancake_v2_address = os.getenv("PANCAKE_V2_CONTRACT_ADDRESS")  # replace with your contract address

app.marketplace_contract = app.w3.eth.contract(address=contract_address, abi=marketplace_abi)
app.token_contract = app.w3.eth.contract(address=token_address, abi=token_abi)
app.pancake_v2_contract = app.w3.eth.contract(address=pancake_v2_address, abi=pancake_abi)

print(app.account.address)

app.w3.eth.defaultAccount = app.account.address
app.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

provided_key = os.getenv("SECRET_KEY").encode() # This should be a bytes-like object
provided_salt = os.getenv("SECRET_SALT").encode()  # This should be a bytes-like object

kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=provided_salt,
    iterations=100000,
    backend=default_backend()
)

key = base64.urlsafe_b64encode(kdf.derive(provided_key))
app.cipher_suite = Fernet(key)

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
    
class CreateWallet(BaseModel):
    userId: str
    
class RegisterRentRequest(BaseModel):
    builderId: str
    providerId: str
    dataURL: str
    ratePerHour: str
    totalHours: str
    rentId: str
    
class EndRentRequest(BaseModel):
    builderId: str
    providerId: str
    totalHours: str
    rentId: str
    
class ErrorRequest(BaseModel):
    builderId: str
    providerId: str
    rentId: str
    reason: str
    
class WithdrawOnChainRequest(BaseModel):
    userId: str
    amount: str
    walletAddress: str

class WithdrawOffChainRequest(BaseModel):
    userId: str
    amount: str
    country: str
    email: EmailStr
    
class WalletResponse(BaseModel):
    userId: str
    walletAddress: str
    balance: str
    pendingBalance: str


class TokenResponse(BaseModel):
    address: str
    name: str
    symbol: str
    price: str
    amountPerDollar: str

class DepositTokensModel(BaseModel):
    amount: float

class StartSessionModel(BaseModel):
    resourceId: int

class EndSessionModel(BaseModel):
    sessionId: int

class WithdrawTokensModel(BaseModel):
    amount: float


class UpdateResourceModel(BaseModel):
    resourceId: int
    cpu: Optional[int] = None
    gpu: Optional[int] = None
    ram: Optional[int] = None
    disk: Optional[int] = None
    price_per_hour: Optional[float] = None
    max_concurrent_sessions: Optional[int] = None

class SessionDetailModel(BaseModel):
    sessionId: int
    
scheduler = AsyncIOScheduler()


async def token_price_job():
    print('job run')
    await get_token_price()

scheduler.add_job(token_price_job, 'interval', minutes=1)


@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient('mongodb://admin:admin123@localhost:27017/')
    app.mongodb = app.mongodb_client['wow']
    app.r = await aioredis.from_url('redis://localhost')
    app.queue = asyncio.Queue()
    scheduler.start()
    
@app.get("/price")
async def get_token_price_data():
    token_list = await get_all_token({})
    
    token_list_response = []
    
    for token in token_list:
        token_list_response.append(TokenResponse(
            address=token.get("address", "Unknown"),
            name=token.get("name", "Unknown"),
            symbol=token.get("symbol", "Unknown"),
            decimal=token.get("decimal", 0),
            price= str(Decimal(1) / Decimal(token.get("amountPerDollar", 1))) if token.get("amountPerDollar", 0) != 0 else "0",
            amountPerDollar=token.get("amountPerDollar", "Unknown")
            
        ))

    return { "data": token_list_response }

@app.post("/wallet")
async def register_resource(resource: CreateWallet):
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    account = Account.from_key(private_key)
    print(private_key)
    hash_private_key = encrypt_private_key(private_key)
    wallet = Wallet(userId=resource.userId, walletAddress=account.address.lower(), privateKey=hash_private_key)
    print(decrypt_private_key(hash_private_key))
    save_wallet = await create_item_if_not_exist(wallet)
        
    wallet_response = WalletResponse(
        userId=save_wallet["userId"],
        walletAddress=save_wallet["walletAddress"],
        role=save_wallet["role"],
    )

    return { "data": wallet_response }

@app.get("/wallet/{user_id}")
async def get_resource(user_id: str):
    # Assuming `db` is your database object and `get_resource` is a function that retrieves a resource by its ID
    wallet = await get_one_by_user_id(user_id)
    if Wallet is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    response_wallet = WalletResponse(
        userId=wallet["userId"],
        walletAddress=wallet["walletAddress"],
        balance=wallet["balance"],
        pendingBalance=wallet["pendingBalance"],
    )
    return { "data": response_wallet }

@app.post("/resource/rent")
async def rent_resource(body: RegisterRentRequest):
    await register_rent(body.builderId, body.providerId, body.dataURL, body.ratePerHour, body.totalHours, body.rentId)
    return {"message": "Rent success"}

@app.post("/resource/end")
async def finish_rent_resource(body: EndRentRequest):
    await end_rent(body.builderId, body.providerId, body.totalHours, body.rentId)
    return {"message": "End rent success"}

@app.post("/resource/error")
async def finish_error_resource(body: ErrorRequest):
    await error_resource(body.builderId, body.providerId, body.rentId, body.reason)
    return {"message": "End rent success"}

def is_valid_address(address: str) -> bool:
    return Web3.is_address(address)

@app.get("/withdraw/off-ramp")
async def get_off_ramp_request(status: Optional[str] = None, userId: Optional[str] = None):
    # await withdraw_token_off_ramp(body.userId, body.amount, body.email, body.country)
    query = {}
    if status is not None:   
        if status.lower() == str(TransferStatus.SUCCESS.value).lower():
            query["status"] = TransferStatus.SUCCESS.value

        elif status.lower() == str(TransferStatus.FAILED.value).lower():
            query["status"] = TransferStatus.FAILED.value
            
        elif status.lower() == str(TransferStatus.REJECT.value).lower():
            query["status"] = TransferStatus.REJECT.value

        elif status.lower() == str(TransferStatus.IS_PROCESSING.value).lower():
            query["status"] = TransferStatus.IS_PROCESSING.value

    if userId is not None:   
        query["userId"] = userId


    transaction_requests = await get_transfer_off_ramp_by_status(query)
    transaction_requests = [{**req, '_id': str(req['_id'])} for req in transaction_requests]
    return {"data": transaction_requests}


@app.get("/withdraw/off-ramp/{id}")
async def get_off_ramp_request_by_id(id: str):
    

    transaction_request = await get_one_transfer_off_ramp_request({"_id": ObjectId(id)})
    
    return {"data": transaction_request}

@app.post("/withdraw/on-ramp")
async def withdraw_token_request(body: WithdrawOnChainRequest):
    if not is_valid_address(body.walletAddress):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    await withdraw_token_on_ramp(body.userId, body.amount, app.w3.to_checksum_address(body.walletAddress))
    return {"message": "Create on ramp request success"}

@app.post("/withdraw/off-ramp")
async def withdraw_token_off_ramp_request(body: WithdrawOffChainRequest):
    await withdraw_token_off_ramp(body.userId, body.amount, body.email, body.country)
    return {"message": "Create off ramp request success"}

@app.put("/withdraw/off-ramp/completed/{id}")
async def completed_transfer_request(id: str):
    print(id)
    await update_status(id, TransferStatus.SUCCESS.value)
    
    return {"message": "Complete transfer request success"}

@app.put("/withdraw/off-ramp/reject/{id}")
async def reject_transfer_request(id: str):
    print(id)
    await update_status(id, TransferStatus.REJECT.value)
    
    return {"message": "Reject transfer request success"}

