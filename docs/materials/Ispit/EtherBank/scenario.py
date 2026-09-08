AUTHENTICATION_URL = "http://localhost:5000"
ADMINISTRATOR_URL = "http://localhost:5001"
USER_URL = "http://localhost:5002"
BLOCKCHAIN_URL = "http://127.0.0.1:8545"

import secrets

import requests
from web3 import Account, HTTPProvider, Web3

web3 = Web3(HTTPProvider(BLOCKCHAIN_URL))


def create_and_initialize_account():
    # create account
    private_key = "0x" + secrets.token_hex(32)
    account = Account.from_key(private_key)
    address = account.address

    # send funds from account 0
    result = web3.eth.send_transaction(
        {
            "from": web3.eth.accounts[0],
            "to": address,
            "value": web3.to_wei(2, "ether"),
            "gasPrice": 1,
        }
    )

    return (address, private_key)


def send_transaction(transaction, private_key):
    signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
    transaction_hash = web3.eth.send_raw_transaction(signed_transaction.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    return receipt


user_address, user_private_key = create_and_initialize_account()

result = requests.post(
    url=AUTHENTICATION_URL + "/register",
    json={"email": "user@google.com", "password": "1", "account_address": user_address},
)

user_id = result.json()["id"]

result = requests.post(
    url=AUTHENTICATION_URL + "/login", json={"email": "user@google.com", "password": "1"}
)

user_access_token = result.json()["access_token"]

result = requests.post(
    url=AUTHENTICATION_URL + "/login", json={"email": "admin@google.com", "password": "1"}
)

admin_access_token = result.json()["access_token"]

result = requests.post(
    url=ADMINISTRATOR_URL + "/create_account",
    headers={"Authorization": f"Bearer {admin_access_token}"},
    json={"user_id": user_id},
)

account_id = result.json()["id"]

result = requests.post(
    url=USER_URL + f"/create_deposit_invoice/{account_id}/1000",
    headers={"Authorization": f"Bearer {user_access_token}"},
)

transaction = result.json()["transaction"]

send_transaction(transaction, user_private_key)

result = requests.get(
    url=USER_URL + f"/get_balance/{account_id}",
    headers={"Authorization": f"Bearer {user_access_token}"},
)

balance = result.json()["balance"]

result = requests.post(
    url=USER_URL + f"/create_withdraw_invoice/{account_id}/100",
    headers={"Authorization": f"Bearer {user_access_token}"},
)

transaction = result.json()["transaction"]

send_transaction(transaction, user_private_key)

result = requests.get(
    url=USER_URL + f"/get_balance/{account_id}",
    headers={"Authorization": f"Bearer {user_access_token}"},
)

balance = result.json()["balance"]
