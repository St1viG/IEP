import os

from flask import Flask, jsonify, request

import utilities
from configuration import Configuration
from models import Delivery, Package, database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)


@application.route("/take_package", methods=["POST"])
def take_package():
    courier_id = request.json.get("courier_id", 0)
    package_id = request.json.get("package_id", 0)
    courier_address = request.json.get("courier_address", 0)
    customer_address = request.json.get("customer_address", 0)

    package = Package.query.filter(Package.id == package_id).one()
    if not package:
        return ("Invalid package id!", 400)

    abi = utilities.read_file("./output/Delivery.abi")
    bytecode = utilities.read_file("./output/Delivery.bin")

    web3 = utilities.get_web3()

    contract = web3.eth.contract(bytecode=bytecode, abi=abi)

    owner_address = utilities.get_owner_account()[0]

    create_contract_transaction = contract.constructor(
        owner_address, courier_address, customer_address, package.delivery_price
    ).build_transaction(
        {
            "from": owner_address,
            "nonce": web3.eth.get_transaction_count(owner_address),
            "gasPrice": 1,
        }
    )

    owner_private_key = utilities.get_owner_account()[1]

    receipt = utilities.send_transaction(create_contract_transaction, owner_private_key)

    contract_address = receipt["contractAddress"]

    new_delivery = Delivery(
        contract_address=contract_address, courier_id=courier_id, package_id=package_id
    )

    database.session.add(new_delivery)
    database.session.commit()

    return jsonify(id=new_delivery.id)


if __name__ == "__main__":
    PORT = os.environ["PORT"] if ("PORT" in os.environ) else "5000"
    HOST = "0.0.0.0" if ("PRODUCTION" in os.environ) else "localhost"

    application.run(debug=True, port=PORT, host=HOST)
