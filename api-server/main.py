from fastapi import FastAPI, HTTPException, Response, Body, Depends, status, Request, HTTPException
from web3 import Web3
import os
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Callable
from motor.motor_asyncio import AsyncIOMotorClient
import secrets
from eth_account import Account
from model import Wallet  # assuming you have a Pydantic model named Item
from service import create_item_if_not_exist, get_one_by_user_id, register_rent, encrypt_private_key, worker_operator, end_rent, error_resource, withdraw_token_on_ramp, worker_transfer, withdraw_token_off_ramp , get_transfer_off_ramp_by_status, update_status, get_one_transfer_off_ramp_request, get_token_price, get_all_token # assuming you have a Pydantic model named Item
from bson import ObjectId
import aioredis
import asyncio
from web3.middleware import geth_poa_middleware
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from utils import marketplace_abi, token_abi, TransferStatus, pancake_abi
from decimal import Decimal
import base64
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx

load_dotenv()
global app
app = FastAPI()

mongo_host = os.getenv('MONGODB_HOST', 'mongodb://admin:admin123@localhost:27017/')
redis_host = os.getenv('REDIS_HOST', 'redis://localhost')
OAUTH_SERVER_URL = os.getenv('OAUTH_SERVER_URL', 'http://108.181.196.144:8080')

# Setup Web3 connection
app.w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))
private_key = os.getenv("PRIVATE_KEY_OPERATOR")
app.account = Account.from_key(private_key)

assert app.w3.is_connected()
contract_address = os.getenv("MARKETPLACE_CONTRACT_ADDRESS")  # replace with your contract address
token_address = os.getenv("AXB_CONTRACT_ADDRESS")  # replace with your contract address
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

class RegisterRentRequest(BaseModel):
    providerId: str
    dataURL: str
    ratePerHour: str
    totalHours: str
    rentId: str
    rentId: str
    startTime: str
    
class EndRentRequest(BaseModel):
    providerId: str
    totalHours: str
    rentId: str
    
class ErrorRequest(BaseModel):
    providerId: str
    rentId: str
    reason: str
    
class WithdrawOnChainRequest(BaseModel):
    amount: str
    walletAddress: str

class WithdrawOffChainRequest(BaseModel):
    amount: str
    country: str
    email: EmailStr
    
class WalletResponse(BaseModel):
    walletAddress: str
    userId: str
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
    app.mongodb_client = AsyncIOMotorClient(mongo_host)
    app.mongodb = app.mongodb_client['wow']
    app.r = await aioredis.from_url(redis_host)
    app.queue_transfer = asyncio.Queue()
    app.queue_operator = asyncio.Queue()
    asyncio.create_task(worker_transfer())
    asyncio.create_task(worker_operator())
    scheduler.start()

class TokenData(BaseModel):
    username: str
    authCode: str
    grantType: str
    scope: Optional[str]

WHITELISTED_ROUTES = ["/api/price", "/docs", "/openapi.json"]


async def get_user_id_from_token(request: Request, call_next: Callable):
    if request.url.path not in WHITELISTED_ROUTES:
        try:
            authorization: str = request.headers.get('Authorization')
            if not authorization:
                raise HTTPException(status_code=403, detail="No Authorization header provided")
            
            token = authorization.split(" ")[1]
            url = f"{OAUTH_SERVER_URL}/api/user/info"
            headers = {"Authorization": f"Token {token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=403, detail="Token validation failed")
            
            user_id = response.json().get('data').get('id')
            if not user_id:
                raise HTTPException(status_code=403, detail="User ID not found")
            request.state.user_id = user_id
            
        except HTTPException as e:
            return Response(content=json.dumps({"detail": e.detail}), status_code=e.status_code, media_type='application/json')
    response = await call_next(request)
    return response

app.middleware("http")(get_user_id_from_token)

class TokenData(BaseModel):
    grantType: str
    username: str
    authCode: str
    scope: str = ""
    refresh_token: Optional[str] = None
    userId: str = Field(..., description="User ID")
    
   
@app.get("/api/price")
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

@app.post("/api/wallet")
async def register_resource(request: Request):
    current_user_id = str(request.state.user_id)
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    account = Account.from_key(private_key)
    print(private_key)
    hash_private_key = encrypt_private_key(private_key)
    wallet = Wallet(userId=str(current_user_id), walletAddress=account.address.lower(), privateKey=hash_private_key)
    save_wallet = await create_item_if_not_exist(wallet)
        
    wallet_response = WalletResponse(
        userId=save_wallet["userId"],
        walletAddress=save_wallet["walletAddress"],
        balance=save_wallet["balance"],
        pendingBalance=save_wallet["pendingBalance"],
    )

    return { "data": wallet_response }

@app.get("/api/wallet/me")
async def get_resource(request: Request):
    current_user_id = str(request.state.user_id)
    wallet = await get_one_by_user_id(current_user_id)
    if wallet is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    response_wallet = WalletResponse(
        userId=wallet["userId"],
        walletAddress=wallet["walletAddress"],
        balance=wallet["balance"],
        pendingBalance=wallet["pendingBalance"],
    )
    return { "data": response_wallet }

@app.post("/api/resource/rent")
async def rent_resource(body: RegisterRentRequest, request: Request):
    current_user_id = str(request.state.user_id)
    await register_rent(current_user_id, body.providerId, body.dataURL, body.ratePerHour, body.totalHours, body.rentId)
    return {"message": "Rent success"}

@app.post("/api/resource/end")
async def finish_rent_resource(body: EndRentRequest, request: Request):
    current_user_id = str(request.state.user_id)
    await end_rent(current_user_id, body.providerId, body.totalHours, body.rentId)
    return {"message": "End rent success"}

@app.post("/api/resource/error")
async def finish_error_resource(body: ErrorRequest, request: Request):
    current_user_id = str(request.state.user_id)
    await error_resource(current_user_id, body.providerId, body.rentId, body.reason)
    return {"message": "End rent success"}

def is_valid_address(address: str) -> bool:
    return Web3.is_address(address)

@app.get("/api/withdraw/off-ramp")
async def get_off_ramp_request(request: Request, status: Optional[str] = None, userId: Optional[str] = None):
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


@app.get("/api/withdraw/off-ramp/{id}")
async def get_off_ramp_request_by_id(id: str):
    

    transaction_request = await get_one_transfer_off_ramp_request({"_id": ObjectId(id)})
    
    return {"data": transaction_request}

@app.post("/api/withdraw/on-ramp")
async def withdraw_token_request(body: WithdrawOnChainRequest, request: Request):
    current_user_id = str(request.state.user_id)
    if not is_valid_address(body.walletAddress):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    await withdraw_token_on_ramp(current_user_id, body.amount, app.w3.to_checksum_address(body.walletAddress))
    return {"message": "Create on ramp request success"}

@app.post("/api/withdraw/off-ramp")
async def withdraw_token_off_ramp_request(body: WithdrawOffChainRequest, request: Request):
    current_user_id = str(request.state.user_id)
    await withdraw_token_off_ramp(current_user_id, body.amount, body.email, body.country)
    return {"message": "Create off ramp request success"}

@app.put("/api/withdraw/off-ramp/completed/{id}")
async def completed_transfer_request(id: str, request: Request):
    print(id)
    await update_status(id, TransferStatus.SUCCESS.value)
    
    return {"message": "Complete transfer request success"}

@app.put("/api/withdraw/off-ramp/reject/{id}")
async def reject_transfer_request(id: str, request: Request):
    print(id)
    await update_status(id, TransferStatus.REJECT.value)
    
    return {"message": "Reject transfer request success"}

