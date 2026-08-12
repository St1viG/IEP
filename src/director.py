import json
import threading
import time
from datetime import UTC, datetime

from bson import ObjectId
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from redis import Redis

import utilities
from configuration import Configuration
from decorators import role_check
from validation import missing_field, missing_field_message, valid_uuid

POLL_INTERVAL = 3

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

client = MongoClient(
    host=Configuration.MONGO_HOST,
    port=Configuration.MONGO_PORT,
    username=Configuration.MONGO_USERNAME,
    password=Configuration.MONGO_PASSWORD,
    authSource=Configuration.MONGO_AUTH_SOURCE,
)

assets = client[Configuration.MONGO_DATABASE][Configuration.MONGO_ASSETS]

redis = Redis(host=Configuration.REDIS_HOST, port=Configuration.REDIS_PORT)


def error(message):
    return jsonify(message=message), 400


def shape(order_uuid, order):
    shaped = {"uuid": order_uuid, "order_type": order["order_type"]}

    if order["order_type"] == "BUY":
        shaped["name"] = order["name"]
        shaped["categories"] = order["categories"]
        shaped["info"] = order["info"]
        shaped["buying_price"] = order["buying_price"]
    else:
        shaped["id"] = order["id"]
        shaped["selling_price"] = order["selling_price"]

    return shaped


def apply_order(order):
    moment = datetime.now(UTC)

    if order["order_type"] == "BUY":
        assets.insert_one(
            {
                "name": order["name"],
                "categories": order["categories"],
                "buying_price": order["buying_price"],
                "buying_date": moment,
                "info": order["info"],
            }
        )
    else:
        assets.update_one(
            {"_id": ObjectId(order["id"])},
            {"$set": {"selling_price": order["selling_price"], "selling_date": moment}},
        )


def apply_concluded_votes():
    """One pass over the live contracts, applying whichever have concluded.

    Employees vote at a moment this service takes no part in, so the conclusion
    has to be noticed rather than handled inline. Returns the uuids it settled,
    which is what the tests assert on.
    """

    settled = []

    for key, value in redis.hgetall(Configuration.REDIS_CONTRACTS).items():
        order_uuid, address = key.decode(), value.decode()

        ended, approved = utilities.voting_status(address)

        if not ended:
            continue

        stored = redis.hget(Configuration.REDIS_ORDERS, order_uuid)

        if approved and stored is not None:
            apply_order(json.loads(stored))

        # Either outcome retires the order and the contract.
        redis.hdel(Configuration.REDIS_ORDERS, order_uuid)
        redis.hdel(Configuration.REDIS_CONTRACTS, order_uuid)

        settled.append(order_uuid)

    return settled


def poll_votes(interval=POLL_INTERVAL):
    while True:
        try:
            apply_concluded_votes()
        except Exception as error:  # noqa: BLE001 - a poller that dies stops the whole flow
            application.logger.warning("vote poll failed: %s", error)

        time.sleep(interval)


def start_poller(interval=POLL_INTERVAL):
    thread = threading.Thread(target=poll_votes, args=(interval,), daemon=True)
    thread.start()

    return thread


@application.route("/pending_orders", methods=["GET"])
@role_check("director")
def pending_orders():
    stored = redis.hgetall(Configuration.REDIS_ORDERS)

    return jsonify(orders=[shape(key.decode(), json.loads(value)) for key, value in stored.items()])


@application.route("/decision", methods=["POST"])
@role_check("director")
def decision():
    body = request.get_json(silent=True) or {}

    field = missing_field(body, ["uuid"])

    if field is not None:
        return error(missing_field_message(field))

    if not valid_uuid(body["uuid"]):
        return error("Invalid uuid.")

    if redis.hget(Configuration.REDIS_ORDERS, body["uuid"]) is None:
        return error("Invalid uuid.")

    # "voters" counts as missing when the list is empty, which is the spec's own
    # wording. A value that is not a list at all cannot be a non-empty list of
    # addresses either, so it lands here too.
    voters = body.get("voters")

    if not isinstance(voters, list) or len(voters) == 0:
        return error(missing_field_message("voters"))

    if not all(utilities.valid_address(voter) for voter in voters):
        return error("Invalid voter address.")

    # Checked here as well as in the constructor: the spec asks for this exact
    # message from the endpoint, and a revert would surface as a 500.
    if len(voters) % 2 == 0:
        return error("Even number of voters.")

    address = utilities.deploy_voting(voters)

    # The order stays in Redis until the vote concludes. The poller finds it
    # again through this registry.
    redis.hset(Configuration.REDIS_CONTRACTS, body["uuid"], address)

    approve_transaction, reject_transaction = utilities.vote_transactions(address)

    return jsonify(
        approve_transaction=approve_transaction,
        reject_transaction=reject_transaction,
    )


@application.route("/report", methods=["GET"])
@role_check("director")
def report():
    pipeline = [
        {"$match": {"selling_date": {"$exists": True}, "selling_price": {"$exists": True}}},
        {"$unwind": "$categories"},
        {
            "$group": {
                "_id": "$categories",
                "spent": {"$sum": "$buying_price"},
                "earned": {"$sum": "$selling_price"},
            }
        },
        {"$sort": {"earned": -1, "spent": 1, "_id": 1}},
        {"$project": {"_id": 0, "category": "$_id", "spent": 1, "earned": 1}},
    ]

    return jsonify(statistics=list(assets.aggregate(pipeline)))


if __name__ == "__main__":
    start_poller()

    # use_reloader=False: the reloader runs this module in a second process,
    # which would leave two pollers racing to apply the same approval. For the
    # same reason this service stays at one replica in k8s.yaml.
    application.run(
        debug=True,
        use_reloader=False,
        host=Configuration.HOST,
        port=Configuration.PORT,
    )
