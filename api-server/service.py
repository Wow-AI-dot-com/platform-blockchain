import pickle
from bson import ObjectId
from model import Rent, TransferRequestOnRamp, TransferRequestOffRamp, Token
from typing import List
from decimal import Decimal
from fastapi import HTTPException
from datetime import datetime
from decimal import Decimal
from utils import buffer_amount, TransferRequestType, TransferStatus, get_token_detail
import json
import asyncio
import redis
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
from dotenv import load_dotenv
import os

load_dotenv()

usdt_address = os.getenv("USDT_CONTRACT_ADDRESS")  # replace with your contract address
token_address = os.getenv("TOKEN_CONTRACT_ADDRESS")  # replace with your contract address

async def create_item(item):
    from main import app
    await app.mongodb['wallets'].insert_one(item.dict())
    
async def create_transfer_on_ramp_request(item):
    from main import app
    await app.mongodb['transfer-request-on-ramp'].insert_one(item.dict())
    
async def create_transfer_off_ramp_request(item):
    from main import app
    await app.mongodb['transfer-request-off-ramp'].insert_one(item.dict())

async def find_all_wallet():
    from main import app
    cursor = app.mongodb['wallets'].find()
    wallet_list = await cursor.to_list(length=None)
    return wallet_list
    
async def create_item_if_not_exist(item):
    from main import app
    existing_wallet = await app.mongodb['wallets'].find_one({"userId": item.userId})
    if existing_wallet is None:
        await app.mongodb['wallets'].insert_one(item.dict())
        new_wallet = await app.mongodb['wallets'].find_one({"userId": item.userId})
        new_wallet_list = await find_all_wallet()
        for new_wallet in new_wallet_list:
            if "_id" in new_wallet and isinstance(new_wallet["_id"], ObjectId):
                new_wallet["_id"] = str(new_wallet["_id"])
            if 'privateKey' in new_wallet:
                del new_wallet['privateKey']
        await app.r.set('saved_wallet', json.dumps(new_wallet_list))
        return new_wallet

    return existing_wallet

async def get_wallet(query):
    from main import app
    wallet = await app.mongodb['wallets'].find_one(query)
    return wallet

async def get_by_user_id(user_id):
    from main import app
    cursor = app.mongodb['wallets'].find({"userId": user_id})
    wallets = await cursor.to_list(length=None) 
    return wallets

async def get_one_by_user_id(user_id):
    from main import app
    wallet = await app.mongodb['wallets'].find_one({"userId": user_id})
    return wallet

async def create_rent(item):
    from main import app
    await app.mongodb['rents'].insert_one(item.dict())
    
async def get_rent_by_id(rent_id):
    from main import app
    return await app.mongodb['rents'].find_one({"rentId": rent_id})

async def update_rent(query, update_fields):
    from main import app
    await app.mongodb['rents'].update_one(
        query,  # query
        {"$set": update_fields},  # new values
    )

async def update_wallet(query, update_fields):
    from main import app
    await app.mongodb['wallets'].update_one(
        query,  # query
        {"$set": update_fields},  # new values
    )
    
async def update_token(query, update_fields):
    from main import app
    await app.mongodb['tokens'].update_one(
        query,  # query
        {"$set": update_fields},  # new values
    )

async def get_token(query):
    from main import app
    return await app.mongodb['tokens'].find_one(query)

async def get_all_token(query):
    from main import app
    cursor = app.mongodb['tokens'].find(query)
    tokens = await cursor.to_list(length=None)
    return tokens

    
async def create_token(item):
    from main import app
    await app.mongodb['tokens'].insert_one(item.dict())

async def get_transfer_off_ramp_by_status(query):
    from main import app
    from main import app
    cursor = app.mongodb['transfer-request-off-ramp'].find(query).sort('createdAt', DESCENDING)
    transaction_requests = await cursor.to_list(length=None) 
    return transaction_requests
    
async def get_one_transfer_off_ramp_request(query):
    from main import app
    print(query)
    return await app.mongodb['transfer-request-off-ramp'].find_one(query)

async def update_transfer_request(query, update_fields):
    from main import app
    await app.mongodb['transfer-request-off-ramp'].update_one(
        query,  # query
        {"$set": update_fields},  # new values
    ) 

async def register_rent_blockchain(builder_info,provider_info, rent_id, rate_per_hour, total_hours, data_url, deposit_amount):
    from main import app
    try:
        builder_address_checksum = app.w3.to_checksum_address(builder_info['walletAddress'])
        provider_address_checksum = app.w3.to_checksum_address(provider_info['walletAddress'])
        contract_function = app.marketplace_contract.functions.registerRent(rent_id, builder_address_checksum, provider_address_checksum, rate_per_hour, total_hours, data_url)
        
        gas_estimate = contract_function.estimate_gas()
        transaction = contract_function.build_transaction({
            'chainId': 97,  # This is the mainnet chain ID, replace with your network chain ID
            'gas': gas_estimate,
            'nonce': app.w3.eth.get_transaction_count(app.account.address),
        })
        # # Sign the transaction
        signed_txn = app.w3.eth.account.sign_transaction(transaction, app.account._private_key)

        # # Send the transaction
        txn_hash = app.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(txn_hash.hex())

        # # Wait for the transaction to be mined, and get the transaction receipt
        txn_receipt = app.w3.eth.wait_for_transaction_receipt(txn_hash)
        await update_rent({"rentId": rent_id}, {"isSubmitted": True, "transactionHash": txn_receipt.transactionHash.hex()})
        new_balance = Decimal(builder_info['balance']) - Decimal(deposit_amount)
        await update_wallet({"userId": builder_info['userId']},  {"balance": str(new_balance)} )
        return txn_receipt.transactionHash.hex()
    except Exception as e:
        print(e)
        error_message = str(e)
        if "Already registered" in error_message:
            raise HTTPException(status_code=400, detail="Already registered") 
        else:
            raise HTTPException(status_code=400, detail=error_message) 

async def end_rent_blockchain(builder_info, provider_info, rent_info, total_hours):
    from main import app
    try:
        contract_function = app.marketplace_contract.functions.finishRent(rent_info["rentId"], total_hours)
        
        gas_estimate = contract_function.estimate_gas()
        transaction = contract_function.build_transaction({
            'chainId': 97,  # This is the mainnet chain ID, replace with your network chain ID
            'gas': gas_estimate,
            'nonce': app.w3.eth.get_transaction_count(app.account.address),
        })
        # # Sign the transaction
        signed_txn = app.w3.eth.account.sign_transaction(transaction, app.account._private_key)

        # # Send the transaction
        txn_hash = app.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # # Wait for the transaction to be mined, and get the transaction receipt
        txn_receipt = app.w3.eth.wait_for_transaction_receipt(txn_hash)
        await update_rent({"rentId": rent_info['rentId']}, {"isCompleted": True, "transactionHashCompleted": txn_receipt.transactionHash.hex(), "totalHoursUse": total_hours, "endedAt": datetime.now()})
        pay_amount = Decimal(rent_info['ratePerHour']) * Decimal(total_hours)
        new_balance_provider = Decimal(provider_info['balance']) + Decimal(pay_amount)
        await update_wallet({"userId": provider_info['userId']},  {"balance": str(new_balance_provider)} )
        
        if Decimal(pay_amount) < Decimal(rent_info['depositAmount']):
            refund_builder = Decimal(rent_info['depositAmount']) - Decimal(pay_amount)
            new_balance_builder = Decimal(builder_info['balance']) + refund_builder
            
            await update_wallet({"userId": builder_info['userId']},  {"balance": str(new_balance_builder)} )
        return txn_receipt.transactionHash.hex()
    except Exception as e:
        error_message = str(e)
        if "Already completed" in error_message:
            raise HTTPException(status_code=400, detail="Already completed")
        elif "Not registered" in error_message:
            raise HTTPException(status_code=400, detail="Not registered") 
        elif "Already stop" in error_message:
            raise HTTPException(status_code=400, detail="Already stop") 
        else:
            raise HTTPException(status_code=400, detail=error_message) 

async def error_resource_blockchain(builder_info, rent_info, reason):
    from main import app
    try:
        contract_function = app.marketplace_contract.functions.resourceError(rent_info["rentId"], reason)
        
        gas_estimate = contract_function.estimate_gas()
        transaction = contract_function.build_transaction({
            'chainId': 97,  # This is the mainnet chain ID, replace with your network chain ID
            'gas': gas_estimate,
            'nonce': app.w3.eth.get_transaction_count(app.account.address),
        })
        # # Sign the transaction
        signed_txn = app.w3.eth.account.sign_transaction(transaction, app.account._private_key)

        # # Send the transaction
        txn_hash = app.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # # Wait for the transaction to be mined, and get the transaction receipt
        txn_receipt = app.w3.eth.wait_for_transaction_receipt(txn_hash)
        await update_rent({"rentId": rent_info['rentId']}, {"isErrored": True, "transactionHashError": txn_receipt.transactionHash.hex(), "pay_amount": '0', "endedAt": datetime.now()})
        
        new_balance_builder = Decimal(builder_info['balance']) + Decimal(rent_info['depositAmount'])
            
        await update_wallet({"userId": builder_info['userId']},  {"balance": str(new_balance_builder)} )
        return txn_receipt.transactionHash.hex()
    except Exception as e:
        error_message = str(e)
        if "Already completed" in error_message:
            raise HTTPException(status_code=400, detail="Already completed")
        elif "Not registered" in error_message:
            raise HTTPException(status_code=400, detail="Not registered") 
        elif "Error rent" in error_message:
            raise HTTPException(status_code=400, detail="Error rent") 
        else:
            raise HTTPException(status_code=400, detail=error_message) 

async def register_rent(builder_id: str, provider_id: str, data_url: str, rate_per_hour: str, total_hours: str , rent_id: str):
    print(builder_id,provider_id )
    
    builder_info = await get_one_by_user_id(builder_id)
    provider_info = await get_one_by_user_id(provider_id)
    if  provider_info is None or builder_info is None:
        raise HTTPException(status_code=404, detail="Resource not found") 
    else:
        existing_rent = await get_rent_by_id(rent_id)
        deposit_amount = Decimal(rate_per_hour) * Decimal(total_hours) * (Decimal(1) + Decimal(buffer_amount))
        if existing_rent is None: 
            if Decimal(builder_info['balance']) < Decimal(deposit_amount):
                raise HTTPException(status_code=400, detail="Insufficient balance")
            rent = Rent(builderAddress=builder_info['walletAddress'], providerAddress=provider_info['walletAddress'], dataURL=data_url, rentId=rent_id, depositAmount=str(deposit_amount), ratePerHour=rate_per_hour,totalHoursDeposit=total_hours )
            
            await create_rent(rent)
            await register_rent_blockchain(builder_info, provider_info, rent_id, rate_per_hour, total_hours, data_url, deposit_amount)
        else: 
            raise HTTPException(status_code=403, detail="Already exists") 
        
async def end_rent(builder_id: str, provider_id: str, total_hours: str, rent_id: str):
    builder_info = await get_one_by_user_id(builder_id)
    provider_info = await get_one_by_user_id(provider_id)
    if  provider_info is None or builder_info is None:
        raise HTTPException(status_code=404, detail="Resource not found") 
    else:
        existing_rent = await get_rent_by_id(rent_id)
        if existing_rent is None:
            raise HTTPException(status_code=400, detail="Resource not found")
        elif existing_rent is not None and existing_rent['isCompleted'] == True: 
            raise HTTPException(status_code=400, detail="Already completed")
        elif existing_rent is not None and existing_rent['isErrored'] == True: 
            raise HTTPException(status_code=400, detail="Resource removed")
        else :             
            await end_rent_blockchain(builder_info, provider_info, existing_rent, total_hours)
            
async def error_resource(builder_id: str, provider_id: str, rent_id: str, reason: str):
    builder_info = await get_one_by_user_id(builder_id)
    provider_info = await get_one_by_user_id(provider_id)
    if  provider_info is None or builder_info is None:
        raise HTTPException(status_code=404, detail="Resource not found") 
    else:
        existing_rent = await get_rent_by_id(rent_id)
        if existing_rent is None:
            raise HTTPException(status_code=400, detail="Resource not found")
        elif existing_rent is not None and existing_rent['isCompleted'] == True: 
            raise HTTPException(status_code=400, detail="Already completed")
        elif existing_rent is not None and existing_rent['isErrored'] == True: 
            raise HTTPException(status_code=400, detail="Resource removed")
        elif existing_rent is not None and existing_rent['isCompleted'] == False:             
            await error_resource_blockchain(builder_info, existing_rent, reason)
            
def encrypt_private_key(private_key: str):
    from main import app
    return app.cipher_suite.encrypt(private_key.encode())

def decrypt_private_key(hash_private_key: str):
    from main import app
    return app.cipher_suite.decrypt(hash_private_key).decode('utf-8')

async def withdraw_token_on_ramp(user_id: str, amount: str, wallet_address: str):
    from main import app
    existing_wallet = await get_one_by_user_id(user_id)
    if existing_wallet is None: 
        raise HTTPException(status_code=404, detail="User not found")
    elif Decimal(existing_wallet['balance']) < Decimal(amount):
        raise HTTPException(status_code=400, detail="Insufficient balance")
    else:
        current_admin_balance = app.token_contract.functions.balanceOf(app.account.address).call()
        token_with_decimal = Decimal(current_admin_balance)/ Decimal(1e18)
        if token_with_decimal <  Decimal(amount):
            raise HTTPException(status_code=400, detail="Admin run out of token")
        
        new_pending_balance = Decimal(existing_wallet['pendingBalance']) + Decimal(amount)
        new_balance = Decimal(existing_wallet['balance']) - Decimal(amount)
        if new_balance < Decimal(0):
            raise HTTPException(status_code=400, detail="Insufficient balance")    
        
        await update_wallet({"userId": existing_wallet['userId']},  {"balance": str(new_balance), "pendingBalance": str(new_pending_balance)} )
        existing_wallet = await get_one_by_user_id(user_id)
        if "_id" in existing_wallet and isinstance(existing_wallet["_id"], ObjectId):
            existing_wallet["_id"] = str(existing_wallet["_id"])
        task = json.dumps({'existing_wallet': existing_wallet, 'amount': amount, 'wallet_address': wallet_address})
        await app.queue.put(task)

async def worker():
    from main import app
    while True:
        # Wait for a task from the queue
        task = await app.queue.get()
        # Process the task
        print(f'Processing task: {task}')
        task_data = json.loads(task)
        # Mark the task as done
        current_balance = app.token_contract.functions.balanceOf(app.account.address).call()
        parse_balance_decimal = Decimal(current_balance) / Decimal(1e18)
        if(Decimal(parse_balance_decimal) < Decimal(task_data['amount'])):
            current_wallet = await get_wallet({"userId": task_data['existing_wallet']['userId']})
            new_pending_balance = Decimal(current_wallet['pendingBalance']) - Decimal(task_data['amount'])
            new_balance =  Decimal(current_wallet['balance']) + Decimal(task_data['amount'])
            await update_wallet({"userId": task_data['existing_wallet']['userId']}, {"balance": str(new_balance), "pendingBalance": str(new_pending_balance)})
            transfer_request = TransferRequestOnRamp(userId=task_data['existing_wallet']['userId'], type=TransferRequestType.ON_RAMP_REQUEST, fromAddress=app.account.address, toAddress=task_data['wallet_address'], transactionHash=txn_receipt.transactionHash.hex(), tokenAddress=app.token_contract.address, amount=task_data['amount'], status=TransferStatus.FAILED)
            await create_transfer_on_ramp_request(transfer_request)
        else: 
            try:

                contract_function = app.token_contract.functions.transfer(task_data['wallet_address'], int(Decimal(task_data['amount']) * Decimal(1e18)))
        
                gas_estimate = contract_function.estimate_gas(
                {
                    'from': app.account.address
                })
                transaction = contract_function.build_transaction({
                    'chainId': 97,  # This is the mainnet chain ID, replace with your network chain ID
                    'gas': gas_estimate,
                    'nonce': app.w3.eth.get_transaction_count(app.account.address),
                })
                # # Sign the transaction
                signed_txn = app.w3.eth.account.sign_transaction(transaction, app.account._private_key)

                # # Send the transaction
                txn_hash = app.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                print(txn_hash.hex())

                # # Wait for the transaction to be mined, and get the transaction receipt
                txn_receipt = app.w3.eth.wait_for_transaction_receipt(txn_hash)
                transfer_request = TransferRequestOnRamp(userId=task_data['existing_wallet']['userId'], type=TransferRequestType.ON_RAMP_REQUEST, fromAddress=app.account.address, toAddress=task_data['wallet_address'], transactionHash=txn_receipt.transactionHash.hex(), tokenAddress=app.token_contract.address, amount=task_data['amount'], status=TransferStatus.SUCCESS)
                await create_transfer_on_ramp_request(transfer_request)
                    
                print(txn_receipt.transactionHash.hex())
            except Exception as e:
                print('Failed to transfer:',e)
                
        app.queue.task_done()
        
async def withdraw_token_off_ramp(user_id, amount, email, country):
    from main import app
    existing_wallet = await get_one_by_user_id(user_id)
    if existing_wallet is None: 
        raise HTTPException(status_code=404, detail="User not found")
    elif Decimal(existing_wallet['balance']) < Decimal(amount):
        raise HTTPException(status_code=400, detail="Insufficient balance")
    else:       
        new_pending_balance = Decimal(existing_wallet['pendingBalance']) + Decimal(amount)
        new_balance = Decimal(existing_wallet['balance']) - Decimal(amount)
        
        await update_wallet({"userId": existing_wallet['userId']},  {"balance": str(new_balance), "pendingBalance": str(new_pending_balance)} )
        transfer_request = TransferRequestOffRamp(userId=user_id, type=TransferRequestType.OFF_RAMP_REQUEST, country=country, email=email, tokenAddress=app.token_contract.address, amount=amount, status=TransferStatus.PENDING)
        await create_transfer_off_ramp_request(transfer_request)
        

async def update_status(transfer_id, status):
    existing_request = await get_one_transfer_off_ramp_request({"_id": ObjectId(transfer_id)})
    if existing_request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    await update_transfer_request(
        {"_id": ObjectId(transfer_id)},
        {"status": status}
    )      
    
async def get_token_price():
    from main import app
    try:
        amount_out = app.pancake_v2_contract.functions.getAmountsOut(int(Decimal(1e18)), [app.w3.to_checksum_address(usdt_address),app.w3.to_checksum_address(token_address)]).call()
        parse_to_decimal = Decimal(amount_out[1]) / Decimal(1e18)
        existing_token = await get_token({"address": str(token_address).lower()})
        if existing_token is None:
            token_detail = get_token_detail(str(token_address).lower())
            name = token_detail.get("name", "Unknown")
            symbol = token_detail.get("symbol", "Unknown")
            decimal = token_detail.get("decimals", 18)
            
            token = Token(address=str(token_address).lower(), amountPerDollar=str(parse_to_decimal), name=name, symbol=symbol, decimal= decimal)
            await create_token(token)
        else:
            await update_token({"address": str(token_address).lower()}, {"amountPerDollar": str(parse_to_decimal)})
        
    except Exception as e:
        print('Failed to transfer:',e)