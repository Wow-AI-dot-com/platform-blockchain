import os
from web3 import Web3
import asyncio
from eth_account import Account
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import token_abi
from dotenv import load_dotenv
from decimal import Decimal
from web3.middleware import geth_poa_middleware
from telegram import Bot

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))

private_key_admin = os.getenv("PRIVATE_KEY_ADMIN")
account_admin = Account.from_key(private_key_admin)
w3.eth.defaultAccount = account_admin.address
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

operator_wallet_address = os.getenv("OPERATOR_WALLET_ADDRESS")
send_token_wallet_address = os.getenv("SEND_TOKEN_WALLET_ADDRESS")
axb_address = os.getenv("AXB_CONTRACT_ADDRESS")

axb_min_amount = Web3.to_wei(os.getenv("AXB_MIN_AMOUNT", '10000'), 'ether')
native_min_amount = Web3.to_wei(os.getenv("NATIVE_MIN_AMOUNT", '1'), 'ether')
native_transfer_amount = Web3.to_wei(os.getenv("NATIVE_TRANSFER_AMOUNT", '0.1'), 'ether')
axb_transfer_amount = Web3.to_wei(os.getenv("AXB_TRANSFER_AMOUNT", '1000'), 'ether')
chain_id = int(os.getenv("CHAIN_ID", 97))

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
explorer_url = os.getenv("EXPLORER_URL", 'https://testnet.bscscan.com')


axb_contract = w3.eth.contract(address=axb_address, abi=token_abi)

scheduler = AsyncIOScheduler()

assert w3.is_connected()

def get_message(data):
    message = f"""
    *TRANSFER {data['token']}*
    - Amount: `{data['amount']} {data['token']}`
    - From: `{data['from']}`
    - To: `{data['to']}`
    - Tx: [Transaction Url]({explorer_url}/tx/{data['hash']})
    - Remain BNB: `{data['admin_native_balance']} BNB`
    - Remain AXB: `{data['admin_axb_balance']} AXB`
    """
    return message

async def check_balance_job():
    print('check balance')
    operator_native_balance = w3.eth.get_balance(operator_wallet_address)
    send_token_native_balance = w3.eth.get_balance(send_token_wallet_address)
    send_token_axb_balance = axb_contract.functions.balanceOf(send_token_wallet_address).call()
    if Decimal(operator_native_balance) < Decimal(native_min_amount):
        await send_native(operator_wallet_address)
    if Decimal(send_token_native_balance) < Decimal(native_min_amount):
        await send_native(send_token_wallet_address)
    if Decimal(send_token_axb_balance) < Decimal(axb_min_amount):
        await send_axb(send_token_wallet_address)
    
async def send_native(address):
    nonce = w3.eth.get_transaction_count(account_admin.address)
    txn_dict = {
            'to': address,
            'value': native_transfer_amount,  # Sending native_min_amount
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'chainId': chain_id
    }
    signed_txn = w3.eth.account.sign_transaction(txn_dict, account_admin._private_key)
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
    print('send bnb to ', address, txn_receipt.transactionHash.hex())
    await send_telegram_transfer_message({'hash': txn_receipt.transactionHash.hex(), 'amount': Web3.from_wei(native_transfer_amount, 'ether'), 'from': account_admin.address, 'to': address, 'token': 'BNB'})

async def send_axb(address):
    contract_function = axb_contract.functions.transfer(address, int(axb_transfer_amount))

    gas_estimate = contract_function.estimate_gas(
    {
        'from': account_admin.address
    })
    transaction = contract_function.build_transaction({
        'chainId':chain_id,  # This is the mainnet chain ID, replace with your network chain ID
        'gas': gas_estimate,
        'nonce': w3.eth.get_transaction_count(account_admin.address),
    })
    # # Sign the transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, account_admin._private_key)

    # # Send the transaction
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    # # Wait for the transaction to be mined, and get the transaction receipt
    txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
    print('send axb to ', address, txn_receipt.transactionHash.hex())
    await send_telegram_transfer_message({'hash': txn_receipt.transactionHash.hex(), 'amount': Web3.from_wei(axb_transfer_amount, 'ether'), 'from': account_admin.address, 'to': address, 'token': 'AXB'})
    
    
async def send_telegram_transfer_message(data):
    admin_axb_balance = axb_contract.functions.balanceOf(account_admin.address).call()
    admin_native_balance = w3.eth.get_balance(account_admin.address)
    data['admin_axb_balance'] = Web3.from_wei(admin_axb_balance, 'ether')
    data['admin_native_balance'] = Web3.from_wei(admin_native_balance, 'ether')

    message = get_message(data)
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

scheduler.add_job(check_balance_job, 'interval', minutes=1)

async def main():
    try:
        scheduler.start()
        while True:
            await asyncio.sleep(1)  # keep the program running
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    asyncio.run(main())