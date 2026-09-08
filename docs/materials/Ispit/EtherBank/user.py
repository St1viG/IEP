import os

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, get_jwt

import utilities
from configuration import Configuration
from decorators import role_check
from models import Account, database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)

jwt = JWTManager(application)


@application.route("/create_deposit_invoice/<int:account_id>/<int:amount>", methods=["POST"])
@role_check("user")
def create_deposit_invoice(account_id, amount):
    account = Account.query.filter(Account.id == account_id).first()

    if not account:
        return ("Invalid account id!", 400)

    claims = get_jwt()

    account_address = claims["account_address"]

    abi = utilities.read_file("./output/Account.abi")

    web3 = utilities.get_web3()

    contract = web3.eth.contract(address=account.contract_address, abi=abi)

    transaction = contract.functions.deposit().build_transaction(
        {
            "from": account_address,
            "value": amount,
            "nonce": web3.eth.get_transaction_count(account_address),
            "gasPrice": 1,
        }
    )

    return jsonify(transaction=transaction)


@application.route("/create_withdraw_invoice/<int:account_id>/<int:amount>", methods=["POST"])
@role_check("user")
def create_withdraw_invoice(account_id, amount):
    account = Account.query.filter(Account.id == account_id).first()
    if not account:
        return ("Invalid account id!", 400)

    claims = get_jwt()

    account_address = claims["account_address"]

    abi = utilities.read_file("./output/Account.abi")

    web3 = utilities.get_web3()

    contract = web3.eth.contract(address=account.contract_address, abi=abi)

    transaction = contract.functions.withdraw(account_address, amount).build_transaction(
        {
            "from": account_address,
            "nonce": web3.eth.get_transaction_count(account_address),
            "gasPrice": 1,
        }
    )

    return jsonify(transaction=transaction)


@application.route("/get_balance/<int:account_id>", methods=["GET"])
@role_check("user")
def get_balance(account_id):
    account = Account.query.filter(Account.id == account_id).first()
    if not account:
        return ("Invalid account id!", 400)

    claims = get_jwt()

    account_address = claims["account_address"]

    abi = utilities.read_file("./output/Account.abi")

    web3 = utilities.get_web3()

    contract = web3.eth.contract(address=account.contract_address, abi=abi)

    balance = contract.functions.get_balance().call({"from": account_address})

    return jsonify(balance=balance)


if __name__ == "__main__":
    PORT = os.environ["PORT"] if ("PORT" in os.environ) else "5000"
    HOST = "0.0.0.0" if ("PRODUCTION" in os.environ) else "localhost"

    application.run(debug=True, port=PORT, host=HOST)
