OWNER_URL = "http://localhost:5000"
COURIER_URL = "http://localhost:5001"
CUSTOMER_URL = "http://localhost:5002"
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


result = requests.post(
    url=OWNER_URL + "/add_package", json={"description": "Package0", "delivery_price": 100}
)

package_id = result.json()["id"]

result = requests.post(
    url=OWNER_URL + "/add_courier",
    json={"email": "pera@gmail.com", "forename": "Pera", "surname": "Peric"},
)

courier_id = result.json()["id"]

courier_address, courier_private_key = create_and_initialize_account()
customer_address, customer_private_key = create_and_initialize_account()

result = requests.post(
    url=COURIER_URL + "/take_package",
    json={
        "courier_id": courier_id,
        "package_id": package_id,
        "courier_address": courier_address,
        "customer_address": customer_address,
    },
)

delivery_id = result.json()["id"]

result = requests.get(url=CUSTOMER_URL + f"/create_pay_invoice/{delivery_id}/{customer_address}")
transaction = result.json()["transaction"]

send_transaction(transaction, customer_private_key)

result = requests.get(
    url=CUSTOMER_URL + f"/create_confirm_delivery_invoice/{delivery_id}/{customer_address}"
)

transaction = result.json()["transaction"]

send_transaction(transaction, customer_private_key)
