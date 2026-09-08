import os

from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager

import utilities
from configuration import Configuration
from decorators import role_check
from models import Account, User, database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)

jwt = JWTManager(application)


@application.route("/create_account", methods=["POST"])
@role_check("administrator")
def create_account():
    user_id = request.json.get("user_id", 0)

    user = User.query.filter(User.id == user_id).first()
    if not user:
        return ("Invalid user id!", 400)

    administrator_address = utilities.get_administrator_account()[0]

    abi = utilities.read_file("./output/Account.abi")
    bytecode = utilities.read_file("./output/Account.bin")
    web3 = utilities.get_web3()

    contract = web3.eth.contract(bytecode=bytecode, abi=abi)

    create_contract_transaction = contract.constructor(user.account_address).build_transaction(
        {
            "from": administrator_address,
            "nonce": web3.eth.get_transaction_count(administrator_address),
            "gasPrice": 1,
        }
    )

    administrator_private_key = utilities.get_administrator_account()[1]

    receipt = utilities.send_transaction(create_contract_transaction, administrator_private_key)

    contract_address = receipt["contractAddress"]

    new_account = Account(user_id=user_id, contract_address=contract_address)

    database.session.add(new_account)
    database.session.commit()

    return jsonify(id=new_account.id)


if __name__ == "__main__":
    PORT = os.environ["PORT"] if ("PORT" in os.environ) else "5000"
    HOST = "0.0.0.0" if ("PRODUCTION" in os.environ) else "localhost"

    application.run(debug=True, port=PORT, host=HOST)
