import pickle
from bson import ObjectId
from model import Rent, TransferRequestOnRamp, TransferRequestOffRamp, Token
from typing import Dict, Any, List
from decimal import Decimal
from fastapi import HTTPException
from datetime import datetime
from decimal import Decimal
from utils import buffer_amount, TransferRequestType, TransferStatus, get_token_detail, fee, FeeEnum, PRECISION, RentStatus, SecondEnum
import json
import asyncio
import redis
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
from dotenv import load_dotenv
import os
import httpx
import requests
import time

load_dotenv()

usdt_address = os.getenv("USDT_CONTRACT_ADDRESS")  # replace with your contract address
axb_token_address = os.getenv("AXB_CONTRACT_ADDRESS")  # replace with your contract address
wbnb_token_address = os.getenv("WBNB_CONTRACT_ADDRESS")  # replace with your contract address
chain_id = int(os.getenv("CHAIN_ID", 97))

async def create_item(item, session=None):
    from main import app
    await app.mongodb['wallets'].insert_one(item.dict(), session=session)
    
async def create_transfer_on_ramp_request(item, session=None):
    from main import app
    await app.mongodb['transfer-request-on-ramp'].insert_one(item.dict())
    
async def create_transfer_off_ramp_request(item, session=None):
    from main import app
    await app.mongodb['transfer-request-off-ramp'].insert_one(item.dict(), )

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
        existing_wallet = await app.mongodb['wallets'].find_one({"userId": item.userId})
    new_wallet_list = await find_all_wallet()
    for new_wallet in new_wallet_list:
        if "_id" in new_wallet and isinstance(new_wallet["_id"], ObjectId):
            new_wallet["_id"] = str(new_wallet["_id"])
        if 'privateKey' in new_wallet:
            del new_wallet['privateKey']
        if 'createdAt' in new_wallet:
            del new_wallet['createdAt']
        if 'updatedAt' in new_wallet:
            del new_wallet['updatedAt']
    await app.r.set('saved_wallet', json.dumps(new_wallet_list))

    return existing_wallet

async def get_wallet(query):
    from main import app
    wallet = await app.mongodb['wallets'].find_one(query)
    return wallet

async def get_one_by_user_id(user_id):
    from main import app
    wallet = await app.mongodb['wallets'].find_one({"userId": user_id})
    return wallet

async def get_one_wallet(query):
    from main import app
    wallet = await app.mongodb['wallets'].find_one(query)
    return wallet

async def create_rent(item, session=None):
    from main import app
    result = await app.mongodb['rents'].insert_one(item.dict(), session=session)
    return result.inserted_id
    
async def get_rent(query):
    from main import app
    return await app.mongodb['rents'].find_one(query)

async def get_all_rent(query):
    from main import app
    cursor = app.mongodb['rents'].find(query)
    rent_list = await cursor.to_list(length=None)
    return rent_list

async def update_rent(query, update_fields, session=None):
    from main import app
    await app.mongodb['rents'].update_one(
        query,  # query
        {"$set": update_fields},  # new values
        session=session
    )

async def update_wallet(query, update_fields, session=None):
    from main import app
    await app.mongodb['wallets'].update_one(
        query,  # query
        {"$set": update_fields},  # new values
        session=session
    )
    
async def update_token(query, update_fields, session=None):
    from main import app
    await app.mongodb['tokens'].update_one(
        query,  # query
        {"$set": update_fields},  # new values
        session=session
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

async def update_transfer_request(query, update_fields, session=None):
    from main import app
    await app.mongodb['transfer-request-off-ramp'].update_one(
        query,  # query
        {"$set": update_fields},  # new values
        session=session
    ) 
async def upsert_fee(query, update_fields):
    from main import app
    await app.mongodb['fee'].update_one(
        query,  # query
        {"$set": update_fields},  # new values
        upsert=True  # create the document if it doesn't exist
    )
    
    
async def get_resource_rent_price(rateDollarPerHour, totalHours): 
    from main import app
    try:
        gas_price = app.w3.eth.gas_price

        axb_price = await get_token({"name": "AxB"})
        bnb_price = await get_token({"name": "BNB"})
        if axb_price is None or bnb_price is None:
            raise HTTPException(status_code=404, detail="Token price not found")
        create_fee_axb = app.w3.from_wei(Decimal(gas_price) * Decimal(FeeEnum.CREATE_RENT.value), 'ether') * Decimal(bnb_price.get('priceInDollar'))  / Decimal(axb_price.get('amountPerDollar'))
        finish_fee_axb = app.w3.from_wei(Decimal(gas_price) * Decimal(FeeEnum.FINISH_RENT.value), 'ether') * Decimal(bnb_price.get('priceInDollar'))  / Decimal(axb_price.get('amountPerDollar'))
        error_fee_axb = app.w3.from_wei(Decimal(gas_price) * Decimal(FeeEnum.RENT_ERROR.value), 'ether') * Decimal(bnb_price.get('priceInDollar'))  / Decimal(axb_price.get('amountPerDollar'))
        axb_deposit_rent = (Decimal(rateDollarPerHour) * Decimal(totalHours) * Decimal(axb_price.get('priceInDollar')) * Decimal(1.2)).quantize(PRECISION)
        return {"create_fee_axb": str(create_fee_axb), "finish_fee_axb": str(finish_fee_axb), "error_fee_axb": str(error_fee_axb), "axb_deposit_rent": str(axb_deposit_rent) }
    except Exception as e:
        print('Failed to get resource rent price:',e)
        return 0

async def register_rent_blockchain(builder_info, provider_info, rent_id, rate_dollar_per_hour, total_hours_estimate, started_at, ipfs_hash, deposit_amount_axb):
    from main import app
    try:
        existing_rent = await get_rent({'_id': ObjectId(rent_id)})
        builder_address_checksum = app.w3.to_checksum_address(builder_info['wallet_address'])
        provider_address_checksum = app.w3.to_checksum_address(provider_info['wallet_address'])
        contract_function = app.marketplace_contract.functions.registerRent(existing_rent['rentId'], builder_address_checksum, provider_address_checksum, int(started_at), int(total_hours_estimate) * SecondEnum.ONE_HOUR.value,  rate_dollar_per_hour, ipfs_hash)
        
        gas_estimate = contract_function.estimate_gas()
        transaction = contract_function.build_transaction({
            'chainId':chain_id,  # This is the mainnet chain ID, replace with your network chain ID
            'gas': gas_estimate,
            'nonce': app.w3.eth.get_transaction_count(app.account.address),
        })
        # # Sign the transaction
        signed_txn = app.w3.eth.account.sign_transaction(transaction, app.account._private_key)

        # # Send the transaction
        txn_hash = app.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # # Wait for the transaction to be mined, and get the transaction receipt
        txn_receipt = app.w3.eth.wait_for_transaction_receipt(txn_hash)
        await update_rent({"_id": ObjectId(rent_id)}, {'status': RentStatus.IS_SUBMITTED.value, "transactionHash": txn_receipt.transactionHash.hex()})
        
        return txn_receipt.transactionHash.hex()
    except Exception as e:
        error_message = str(e)
        builder = await get_wallet({'_id': ObjectId(builder_info['_id'])})
        new_balance = Decimal(builder['balance']) + Decimal(deposit_amount_axb)
        await update_wallet({"_id": builder['_id']},  {"balance": str(new_balance)} )
        await update_rent({"_id": ObjectId(rent_id)}, {'status': RentStatus.IS_SUBMITTED_ERROR.value,'errorMessage': error_message})
        if "Already registered" in error_message:
            print('Already registered on blockchain')
        else:
            print(error_message) 

async def end_rent_blockchain(builder_info, provider_info, existing_rent_id, ended_at):
    from main import app
    existing_rent = await get_rent({'_id': ObjectId(existing_rent_id)})
    try:
        await update_rent({"_id": ObjectId(existing_rent['_id'])}, {'isProcess': True})

        paid_list = existing_rent['lastPaid']
        last_paid_time = paid_list[-1] if paid_list else existing_rent['startedAt']
        total_paid_in_second = int(ended_at) - int(last_paid_time)
        unpaid_amount = Decimal(existing_rent['axbPaidPerSecond']) * Decimal(total_paid_in_second)
        paid_amount = Decimal(existing_rent['paidAmount']) + Decimal(unpaid_amount)
        contract_function = app.marketplace_contract.functions.finishRent(existing_rent["rentId"], int(ended_at))
        total_hours_use = (Decimal(ended_at) - Decimal(existing_rent['startedAt']) )/ Decimal(SecondEnum.ONE_HOUR.value)
        
        gas_estimate = contract_function.estimate_gas()
        transaction = contract_function.build_transaction({
            'chainId': chain_id,
            'gas': gas_estimate,
            'nonce': app.w3.eth.get_transaction_count(app.account.address),
        })
        # # Sign the transaction
        signed_txn = app.w3.eth.account.sign_transaction(transaction, app.account._private_key)

        # # Send the transaction
        txn_hash = app.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # # Wait for the transaction to be mined, and get the transaction receipt
        txn_receipt = app.w3.eth.wait_for_transaction_receipt(txn_hash)
        await update_rent({"_id": ObjectId(existing_rent['_id'])}, {"status": RentStatus.COMPLETED.value, 'isProcess': False, "transactionHashCompleted": txn_receipt.transactionHash.hex(), "totalHoursUse": str(total_hours_use), "endedAt": ended_at,  "paidAmount": str(paid_amount)})
        # pay_amount = Decimal(rent_info['ratePerHour']) * Decimal(total_hours)
        existing_provider = await get_wallet({"_id": ObjectId(provider_info['_id'])})
        new_balance_provider = Decimal(existing_provider['balance']) + unpaid_amount
        await update_wallet({"_id": ObjectId(provider_info['_id'])},  {"balance": str(new_balance_provider)} )
        
        if Decimal(paid_amount) < Decimal(existing_rent['depositAmountAxB']):
            print(existing_rent['fee'])
            fee = existing_rent['fee']
            refund_builder = Decimal(existing_rent['depositAmountAxB']) - Decimal(paid_amount) - Decimal(fee['create_fee_axb']) -  Decimal(fee['finish_fee_axb'])
            existing_builder = await get_wallet({"_id": ObjectId(builder_info['_id'])})
            new_balance_builder = Decimal(existing_builder['balance']) + refund_builder
            
            await update_wallet({"_id": ObjectId(builder_info['_id'])},  {"balance": str(new_balance_builder)} )
        return txn_receipt.transactionHash.hex()
    except Exception as e:
        error_message = str(e)
        await update_rent({"_id": ObjectId(existing_rent['_id'])}, {'isProcess': False})
        if "Already completed" in error_message:
            raise HTTPException(status_code=400, detail="Already completed")
        elif "Not registered" in error_message:
            raise HTTPException(status_code=400, detail="Not registered") 
        elif "Already stop" in error_message:
            raise HTTPException(status_code=400, detail="Already stop") 
        else:
            raise HTTPException(status_code=400, detail=error_message) 

async def error_resource_blockchain(builder_info, existing_rent_id, reason):
    from main import app
    try:
        existing_builder = await get_one_wallet({"_id": ObjectId(builder_info['_id'])})
        existing_rent = await get_rent({"_id": ObjectId(existing_rent_id)})

        print(existing_rent)
        contract_function = app.marketplace_contract.functions.resourceError(existing_rent["rentId"], reason)
        
        gas_estimate = contract_function.estimate_gas()
        transaction = contract_function.build_transaction({
            'chainId':chain_id,  # This is the mainnet chain ID, replace with your network chain ID
            'gas': gas_estimate,
            'nonce': app.w3.eth.get_transaction_count(app.account.address),
        })
        # # Sign the transaction
        signed_txn = app.w3.eth.account.sign_transaction(transaction, app.account._private_key)

        # # Send the transaction
        txn_hash = app.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # # Wait for the transaction to be mined, and get the transaction receipt
        txn_receipt = app.w3.eth.wait_for_transaction_receipt(txn_hash)
        await update_rent({"_id": ObjectId(existing_rent['_id'])}, {"status": RentStatus.IS_ERROR_RESOURCE.value, "transactionHashError": txn_receipt.transactionHash.hex(), "pay_amount": '0', "endedAt": datetime.now()})
        
        new_balance_builder = Decimal(existing_builder['balance']) + Decimal(existing_rent['depositAmountAxB']) - Decimal(existing_rent['fee']['createFeeAxB']) - Decimal(existing_rent['fee']['errorFeeAxB'])
            
        await update_wallet({"userId": existing_builder['userId']},  {"balance": str(new_balance_builder)} )
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
        
async def pin_json_to_ipfs(data):
    pinata_api_url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "pinata_api_key": os.getenv("PINATA_API_KEY"),
        "pinata_secret_api_key": os.getenv("PINATA_SECRET_KEY"),
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(pinata_api_url, headers=headers, data=json.dumps(data))
    return response.json().get('IpfsHash')

async def process_rent(i, rent_id, provider_id, resource_info, rate_dollar_per_hour, total_hours_estimate, axb_price, create_fee_axb, finish_fee_axb, error_fee_axb):
    existing_rent = await get_rent({"rentId": rent_id[i]})
    provider_info = await get_one_by_user_id(provider_id[i])
    if provider_info is None:
        raise HTTPException(status_code=404, detail="provider not found") 
    if existing_rent is None: 
        amount_axb = Decimal(rate_dollar_per_hour[i]) * Decimal(total_hours_estimate[i]) * Decimal(axb_price.get('amountPerDollar'))
        total_deposit_amount_axb = ((amount_axb * (Decimal(1) + Decimal(buffer_amount))) + create_fee_axb + finish_fee_axb + error_fee_axb)
        ipfs_hash = await pin_json_to_ipfs(resource_info[i])
        return {
            "rentId": rent_id[i],
            "depositAmountAxb": total_deposit_amount_axb,
            "ipfsHash": ipfs_hash,
            'createFeeAxB': str(create_fee_axb),
            'finishFeeAxB': str(finish_fee_axb),
            'errorFeeAxB': str(error_fee_axb)
        }
    else: 
        raise HTTPException(status_code=403, detail="Already exists")  



async def calculate_deposit_amount(rent_id: List[str], provider_id: List[str], resource_info: List[Dict[str, Any]],rate_dollar_per_hour: List[str], total_hours_estimate: List[str]):
    from main import app
    axb_price = await get_token({"name": "AxB"})
    bnb_price = await get_token({"name": "BNB"})
    if axb_price is None or bnb_price is None:
        raise HTTPException(status_code=400, detail="Get AxB price failed") 
    gas_price = app.w3.eth.gas_price
    create_fee_axb = app.w3.from_wei(Decimal(gas_price) * Decimal(FeeEnum.CREATE_RENT.value), 'ether') * Decimal(bnb_price.get('priceInDollar'))  / Decimal(axb_price.get('amountPerDollar'))
    finish_fee_axb = app.w3.from_wei(Decimal(gas_price) * Decimal(FeeEnum.FINISH_RENT.value), 'ether') * Decimal(bnb_price.get('priceInDollar'))  / Decimal(axb_price.get('amountPerDollar'))
    error_fee_axb = app.w3.from_wei(Decimal(gas_price) * Decimal(FeeEnum.RENT_ERROR.value), 'ether') * Decimal(bnb_price.get('priceInDollar'))  / Decimal(axb_price.get('amountPerDollar'))
    total_deposit_response = {
        'totalDepositAxB' : Decimal(0),
        'rentDetail' : [],
    }
    tasks = [process_rent(i, rent_id, provider_id, resource_info, rate_dollar_per_hour, total_hours_estimate, axb_price, create_fee_axb, finish_fee_axb, error_fee_axb) for i in range(len(rate_dollar_per_hour))]
    results = await asyncio.gather(*tasks)
    for result in results:
        total_deposit_response['totalDepositAxB'] += result['depositAmountAxb']
        total_deposit_response['rentDetail'].append(result)
    return total_deposit_response


async def register_rent(builder_id: str, provider_id: List[str], resource_info: List[Dict[str, Any]], rate_dollar_per_hour: List[str], total_hours_estimate: List[str] , rent_id: List[str], started_at: List[str]):
    from main import app
    
    builder_info = await get_one_by_user_id(builder_id)
    if  builder_info is None:
        raise HTTPException(status_code=404, detail="builder not found") 
    response = []
    try:
        deposit_response = await calculate_deposit_amount(rent_id, provider_id, resource_info, rate_dollar_per_hour, total_hours_estimate)
        print(len(deposit_response))
        if Decimal(builder_info['balance']) < Decimal(deposit_response['totalDepositAxB']):
            raise HTTPException(status_code=400, detail="Insufficient balance")
        new_balance = Decimal(builder_info['balance']) - Decimal(deposit_response['totalDepositAxB'])
        await update_wallet({"userId": builder_info['userId']},  {"balance": str(new_balance)} )
        tasks = []
        for i in range(len(provider_id)):
            deposit_detail = deposit_response['rentDetail'][i]
            provider_info = await get_one_by_user_id(provider_id[i])
            rent = Rent(
                builderAddress=builder_info['walletAddress'], 
                providerAddress=provider_info['walletAddress'], 
                ipfsHash=deposit_detail['ipfsHash'], rentId=rent_id[i], 
                depositAmountAxB=str(deposit_detail['depositAmountAxb']), 
                rateDollarPerHour=rate_dollar_per_hour[i],
                totalHoursEstimate=total_hours_estimate[i], 
                axbPaidPerSecond= str(deposit_detail['depositAmountAxb'] / Decimal(total_hours_estimate[i]) / Decimal(SecondEnum.ONE_HOUR.value)),
                startedAt=started_at[i], 
                fee= json.dumps({
                    'createFeeAxB': deposit_detail['createFeeAxB'],
                    'finishFeeAxB': deposit_detail['finishFeeAxB'],
                    'errorFeeAxB': deposit_detail['errorFeeAxB']
                })
            )

            inserted_rent_id = await create_rent(rent)
            task = json.dumps({ 'type': "register_rent", 'rent_info': 
                { 'builder_info': { "_id": str(builder_info['_id']), "wallet_address": str(builder_info['walletAddress']) }, 
                'provider_info': { "_id": str(provider_info['_id']), "wallet_address": str(provider_info['walletAddress']) }, 
                'rent_id': str(inserted_rent_id), 
                'rate_dollar_per_hour': rate_dollar_per_hour[i], 
                'total_hours_estimate': total_hours_estimate[i], 
                'started_at': started_at[i], 
                'ipfs_hash': deposit_detail['ipfsHash'], 
                'deposit_amount_axb': str(deposit_detail['depositAmountAxb']), } })
            tasks.append(task)
            response.append({
                "rentId": rent_id[i],
                "depositAmountAxb": str(deposit_detail['depositAmountAxb']),
                "ipfsHash": deposit_detail['ipfsHash'],
                "fee": {
                    'create_fee_axb': deposit_detail['createFeeAxB'],
                    'finish_fee_axb': deposit_detail['finishFeeAxB'],
                    'error_fee_axb': deposit_detail['errorFeeAxB']
                }
            })
        await asyncio.gather(*(app.queue_operator.put(task) for task in tasks))        
        return response
    except Exception as e:
        print(e)
        raise e
       
        
async def end_rent(builder_id: str, ended_at: str, rent_id: str):
    from main import app
    
    existing_rent = await get_rent({"rentId": rent_id})
    if existing_rent is None:
        raise HTTPException(status_code=400, detail="Resource not found")
    builder_info = await get_wallet({"userId": builder_id})
    
    if builder_info is None or builder_info['walletAddress'] != existing_rent['builderAddress']:
        raise HTTPException(status_code=400, detail="Invalid user")
    provider_info = await get_wallet({"walletAddress": existing_rent['providerAddress']})
    if  provider_info is None or builder_info is None:
        raise HTTPException(status_code=404, detail="User not found") 
    else:
        if existing_rent['status'] == RentStatus.IS_SUBMITTED.value: 
            await update_rent({"_id": ObjectId(existing_rent['_id'])}, {"isProcess": True})
            task = json.dumps({'type': "end_rent", 'end_rent_info': {
                'builder_info': { "_id": str(builder_info['_id']), "wallet_address": str(builder_info['walletAddress']) }, 
                'provider_info': { "_id": str(provider_info['_id']), "wallet_address": str(provider_info['walletAddress']) }, 
                'existing_rent_id': str(existing_rent['_id']), 
                'ended_at': ended_at
            }})
            await app.queue_operator.put(task)
        elif existing_rent['status'] == RentStatus.COMPLETED.value: 
            raise HTTPException(status_code=400, detail="Already completed")
        elif existing_rent['status'] == RentStatus.IS_ERROR_RESOURCE.value: 
            raise HTTPException(status_code=400, detail="Resource removed due to error")
        elif existing_rent['status'] == RentStatus.IS_SUBMITTED_ERROR.value: 
            raise HTTPException(status_code=400, detail="Resource not submitted to blockchain yet")
        elif existing_rent['status'] == RentStatus.PENDING.value: 
            raise HTTPException(status_code=400, detail="Resource is waiting to submit to blockchain")    
        else: 
            raise HTTPException(status_code=400, detail="End resource fail")
            
async def error_resource(builder_id: str, rent_id: str, reason: str):
    from main import app
    builder_info = await get_one_by_user_id(builder_id)
    if  builder_info is None:
        raise HTTPException(status_code=404, detail="Resource not found") 
    else:
        existing_rent = await get_rent({"rentId": rent_id})
        print(existing_rent)
        if existing_rent['builderAddress'] != builder_info['walletAddress']:
            raise HTTPException(status_code=400, detail="Invalid user")
        else:
            if existing_rent is None:
                raise HTTPException(status_code=400, detail="Resource not found")
            elif existing_rent['status'] == RentStatus.IS_SUBMITTED_ERROR.value: 
                raise HTTPException(status_code=400, detail="Already completed")
            elif existing_rent['status'] == RentStatus.COMPLETED.value: 
                raise HTTPException(status_code=400, detail="Already completed")
            elif existing_rent['status'] == RentStatus.IS_ERROR_RESOURCE.value: 
                raise HTTPException(status_code=400, detail="Resource removed")
            elif existing_rent['status'] == RentStatus.IS_SUBMITTED.value:
                task = json.dumps({'type': "rent_error", 'rent_error_info': {
                    'builder_info': { "_id": str(builder_info['_id']), "wallet_address": str(builder_info['walletAddress']) }, 
                    'existing_rent_id': str(existing_rent['_id']), 
                    'reason': reason
                }})
                await app.queue_operator.put(task)
            else:
                raise HTTPException(status_code=400, detail="Rent rent fail")

async def worker_operator():
    from main import app
    while True:
        task = await app.queue_operator.get()
        # Process the task
        task_data = json.loads(task)
        print(f'Processing task: {task_data}')
        
        if(task_data['type'] == "register_rent"):
            rent_info = task_data['rent_info']
            await register_rent_blockchain(rent_info["builder_info"], rent_info['provider_info'], rent_info['rent_id'], rent_info['rate_dollar_per_hour'], rent_info['total_hours_estimate'], rent_info['started_at'], rent_info['ipfs_hash'], rent_info['deposit_amount_axb'])
        elif(task_data['type'] == "end_rent"):
            end_rent_info = task_data['end_rent_info']
            await end_rent_blockchain(end_rent_info['builder_info'], end_rent_info['provider_info'], end_rent_info['existing_rent_id'], end_rent_info['ended_at'])
        elif(task_data['type'] == "rent_error"):
            rent_error_info = task_data['rent_error_info']
            await error_resource_blockchain(rent_error_info['builder_info'], rent_error_info['existing_rent_id'], rent_error_info['reason'])
        app.queue_operator.task_done()
          
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
        if 'privateKey' in existing_wallet:
            del existing_wallet['privateKey']
        if 'createdAt' in existing_wallet:
            del existing_wallet['createdAt']
        if 'updatedAt' in existing_wallet:
            del existing_wallet['updatedAt']
        task = json.dumps({'existing_wallet': existing_wallet, 'amount': amount, 'wallet_address': wallet_address})
        await app.queue_transfer.put(task)

async def worker_transfer():
    from main import app
    while True:
        # Wait for a task from the queue_transfer
        task = await app.queue_transfer.get()
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
                    'chainId': chain_id,  # This is the mainnet chain ID, replace with your network chain ID
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
                
        app.queue_transfer.task_done()
        
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

async def get_bnb_price(): 
    try:
        url_coingecko = 'https://api.coingecko.com/api/v3/simple/price?ids=binancecoin&vs_currencies=usd' 
        async with httpx.AsyncClient() as client:
            response = await client.get(url_coingecko)   
        if response.status_code != 200:
            print('Failed to get BNB price')
        else:
            bnb_price = response.json().get('binancecoin').get('usd')
            token_detail = get_token_detail('bnb')
            existing_token = await get_token({"address": token_detail.get("address").lower()})
            amountPerDollar = str(Decimal(1)/Decimal(bnb_price))
            priceInDollar = str(bnb_price)
            if existing_token is None:
                name = token_detail.get("name", "Unknown")
                symbol = token_detail.get("symbol", "Unknown")
                decimal = token_detail.get("decimals", 18)
                token = Token(address=token_detail.get("address").lower(), amountPerDollar=amountPerDollar, priceInDollar=priceInDollar ,name=name, symbol=symbol, decimal= decimal)
                await create_token(token)
            else:
                await update_token({"address": token_detail.get("address").lower()}, {"amountPerDollar": amountPerDollar, "priceInDollar":priceInDollar})
    except Exception as e:
        print('Failed to get BNB price:',e)

    
async def get_axb_price():
    from main import app
    try:
        amount_out = app.pancake_v2_contract.functions.getAmountsOut(int(Decimal(1e18)), [app.w3.to_checksum_address(usdt_address),app.w3.to_checksum_address(axb_token_address)]).call()
        parse_to_decimal = str(Decimal(amount_out[1]) / Decimal(1e18))
        priceInDollar = str(Decimal(1) / Decimal(parse_to_decimal))
        token_detail = get_token_detail('axb')
        existing_token = await get_token({"address": token_detail.get("address").lower()})
        if existing_token is None:
            name = token_detail.get("name", "Unknown")
            symbol = token_detail.get("symbol", "Unknown")
            decimal = token_detail.get("decimals", 18)
            
            token = Token(address=token_detail.get("address").lower(), amountPerDollar=parse_to_decimal,priceInDollar=priceInDollar, name=name, symbol=symbol, decimal= decimal)
            await create_token(token)
        else:
            await update_token({"address": token_detail.get("address").lower()}, {"amountPerDollar": parse_to_decimal, "priceInDollar": priceInDollar})  
    except Exception as e:
        print('Failed to get AxB price:',e)
        
async def get_fee():
    from main import app
    try:
        gas_price = app.w3.eth.gas_price
        bnb_price = await get_token({"name": "BNB"})
        axb_price = await get_token({"name": "AxB"})
        for item in fee:
            if axb_price is not None and bnb_price is not None and gas_price is not None:
                gasFeeInBNB = app.w3.from_wei(Decimal(gas_price) * Decimal(item.get('gasLimit')), 'ether')      
                gasFeeInDollar = gasFeeInBNB * Decimal(bnb_price.get('priceInDollar'))
                gasFeeInAxB = Decimal(gasFeeInDollar) / Decimal(axb_price.get('amountPerDollar'))
                await upsert_fee({"name": item.get('name')}, {"name": item.get('name'), "gasFeeInDollar": str(gasFeeInDollar), "gasFeeInAxB": str(gasFeeInAxB), "gasFeeInBNB": str(gasFeeInBNB)})
        
    except Exception as e:
        print('Failed to get AxB price:',e)

        
async def get_token_price():
    try:
        await get_bnb_price()
        await get_axb_price()
        await get_fee()
    except Exception as e:
        print('Get token job fail:',e)
        
async def update_rent_balance(rent_info):
    try:
        paid_list = rent_info['lastPaid']

        last_paid_time = paid_list[-1] if paid_list else rent_info['startedAt']
        current_timestamp = int(time.time())
        total_paid_in_second = current_timestamp - int(last_paid_time)
        unpaid_amount = Decimal(rent_info['axbPaidPerSecond']) * Decimal(total_paid_in_second)
        paid_amount = Decimal(rent_info['paidAmount']) + unpaid_amount
        existing_provider = await get_wallet({"walletAddress": rent_info['providerAddress']})
        
        if paid_amount <= Decimal(rent_info['depositAmountAxB']):
            rent_info['lastPaid'].append(current_timestamp)
            new_balance_provider = Decimal(existing_provider['balance']) + unpaid_amount
            await update_rent({"_id": ObjectId(rent_info['_id'])}, { "paidAmount": str(paid_amount), "lastPaid": rent_info['lastPaid'], "isProcess": False})
            
            
        else:
            unpaid_amount = Decimal(rent_info['depositAmountAxB']) - Decimal(rent_info['paidAmount'])
            paid_amount = Decimal(rent_info['depositAmountAxB'])
            print(unpaid_amount)
            if unpaid_amount > Decimal(0):
                rent_info['lastPaid'].append(current_timestamp)
            else: 
                unpaid_amount = Decimal(0)
            new_balance_provider = Decimal(existing_provider['balance']) + unpaid_amount
            await update_rent({"_id": ObjectId(rent_info['_id'])}, { "paidAmount": str(paid_amount), "lastPaid": rent_info['lastPaid'], "isProcess": False, "status": RentStatus.PAID_ALL.value})    

        await update_wallet({"_id": ObjectId(existing_provider['_id'])},  {"balance": str(new_balance_provider)} )
    except Exception as e:
        await update_rent({"_id": ObjectId(rent_info['_id'])}, {"isProcess": False})
        print('An exception occurred', e)

def chunk_list(input_list, chunk_size):
    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]
        
async def update_balance_job():
    try:
        print('update balance job')
        rent_in_process = await get_all_rent({"status": RentStatus.IS_SUBMITTED.value, "isProcess": False})
        for rent in rent_in_process:
            await update_rent({"_id": ObjectId(rent['_id'])}, {"isProcess": True})
            await update_rent_balance(rent)      
    except Exception as e:
        print('Update balance job fail:',e)
        
        
        