import json

from web3 import Account, HTTPProvider, Web3

from configuration import BLOCKCHAIN_URL


def get_web3():
    return Web3(HTTPProvider(BLOCKCHAIN_URL))


def send_transaction(transaction, private_key):
    web3 = get_web3()

    signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
    transaction_hash = web3.eth.send_raw_transaction(signed_transaction.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    return receipt


def read_file(path):
    with open(path) as file:
        return file.read()


def get_owner_account():
    web3 = get_web3()

    data = json.loads(read_file("owner_account.json"))

    address = web3.to_checksum_address(data["address"])
    private_key = Account.decrypt(data, "iepblockchain").hex()

    balance = web3.eth.get_balance(address)

    if balance <= web3.to_wei(1, "ether"):
        result = web3.eth.send_transaction(
            {
                "from": web3.eth.accounts[0],
                "to": address,
                "value": web3.to_wei(2, "ether"),
                "gasPrice": 1,
            }
        )

    return (address, private_key)
