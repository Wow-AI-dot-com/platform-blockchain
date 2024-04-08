    
import json
from web3 import Web3
import asyncio
import redis
from motor.motor_asyncio import AsyncIOMotorClient
import pickle
from model import Transaction  # assuming you have a Pydantic model named Item
from decimal import Decimal
from dotenv import load_dotenv
import os
import aioredis
from bson import ObjectId

from utils import token_abi, get_token_name

load_dotenv()

# Global variable for Redis connection
r = None
# Connect to Ethereum node

# ABI and address of the contract
token_address = os.getenv("AXB_CONTRACT_ADDRESS")  # Replace with your contract's address
usdt_address = os.getenv("USDT_CONTRACT_ADDRESS")  # replace with your contract address

async def set_key(redis, key, value):
    await redis.set(key, value)

async def get_key(redis, key):
    value = await redis.get(key)
    return value


# add your blockchain connection information
web3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))
mongodb_client = AsyncIOMotorClient(os.getenv('MONGODB_HOST', 'mongodb://admin:admin123@localhost:27017/'))
mongodb = mongodb_client['wow']

# uniswap address and abi
contract = web3.eth.contract(address=token_address, abi=token_abi)
usdt_contract = web3.eth.contract(address=usdt_address, abi=token_abi)

def find_in_list(lst, key, value):
    for item in lst:
        if item.get(key) == value:
            return item
    return None


async def find_all_wallet():
    cursor = mongodb['wallets'].find()
    wallet_list = await cursor.to_list(length=None)
    return wallet_list


def create_item(transaction):
    mongodb['transaction'].insert_one(transaction.dict())   
    
async def get_item(wallet_address):
    return await mongodb['wallets'].find_one({"walletAddress": wallet_address})

def update_wallet(wallet_address, update_fields):
    mongodb['wallets'].update_one(
        {"walletAddress": wallet_address.lower()},  # query
        {"$set": update_fields},  # new values
    )
    
async def get_token(query):
    return await mongodb['tokens'].find_one(query)


# define function to handle events and print to the console
async def handle_event(event):
    global r
    list_wallet_cache = await get_key(r, 'saved_wallet')
    if list_wallet_cache is None:
        list_wallet = await find_all_wallet()
        for new_wallet in list_wallet:
            if "_id" in new_wallet and isinstance(new_wallet["_id"], ObjectId):
                new_wallet["_id"] = str(new_wallet["_id"])
            if 'privateKey' in new_wallet:
                del new_wallet['privateKey']
        await set_key(r, 'saved_wallet', json.dumps(list_wallet))
        list_wallet_cache = await get_key(r, 'saved_wallet')
        
    if list_wallet_cache is not None:
        list_wallet = json.loads(list_wallet_cache)

        if len(list_wallet) != 0:
            wallet = find_in_list(list_wallet, 'walletAddress' , event.args.to.lower())
            if wallet is not None:
                token_name = get_token_name(str(event.address).lower())
                transaction = Transaction(fromAddress=str(event.args['from']).lower(), name= token_name, toAddress=str(event.args.to).lower(), transactionHash=event.transactionHash.hex(), tokenAddress=event.address, amount=str(event.args.value), blockNumber=str(event.blockNumber))
                create_item(transaction)
                user = await get_item(event.args.to.lower())
                if user is not None:
                    amount = Decimal(event.args.value)
                    print(event.address, usdt_address)
                    if str(event.address).lower() == str(usdt_address).lower():
                        token_price = await get_token({"address": str(token_address).lower()})
                        if token_price is not None:
                            amount = Decimal(amount) * Decimal(token_price['amountPerDollar'])
                    new_balance = str(Decimal(amount) / (10 ** 18) + Decimal(user.get('balance', 0)))
                    update_wallet(user.get('walletAddress'), {"balance": new_balance})
                            
            


# asynchronous defined function to loop
# this loop sets up an event filter and is looking for new entires for the "PairCreated" event
# this loop runs on a poll interval
async def log_loop(event_filter, poll_interval):
    while True:
        for event in event_filter.get_new_entries():
            if isinstance(event, list):
                for item in event:
                    await handle_event(item)
            else:
                await handle_event(event)
        await asyncio.sleep(poll_interval)


# when main is called
# create a filter for the latest block and look for the "PairCreated" event for the uniswap factory contract
# run an async loop
# try to run the log_loop function above every 2 seconds
async def main():
    global r
    r = await aioredis.from_url(os.getenv('REDIS_HOST', 'redis://localhost'))
    event_token_filter = contract.events.Transfer.create_filter(fromBlock='latest')
    event_usdt_filter = usdt_contract.events.Transfer.create_filter(fromBlock='latest')
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    try:
       await asyncio.gather(
                log_loop(event_token_filter, 2),
                log_loop(event_usdt_filter, 2),
            )
    finally:
        loop.close()


if __name__ == "__main__":
    asyncio.run(main())