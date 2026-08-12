import json
from datetime import UTC, datetime

from bson import ObjectId
from flask import Flask, Response, jsonify, request
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from redis import Redis

from configuration import Configuration
from decorators import role_check
from validation import missing_field, missing_field_message, valid_uuid

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

    stored = redis.hget(Configuration.REDIS_ORDERS, body["uuid"])

    if stored is None:
        return error("Invalid uuid.")

    # The spec grants "approved" no empty-string clause, unlike "uuid", so
    # presence is all that is checked here and "" falls to "Invalid decision.".
    if "approved" not in body:
        return error(missing_field_message("approved"))

    if not isinstance(body["approved"], bool):
        return error("Invalid decision.")

    if body["approved"] is True:
        apply_order(json.loads(stored))

    redis.hdel(Configuration.REDIS_ORDERS, body["uuid"])

    return Response(status=200)


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
    application.run(debug=True, host=Configuration.HOST, port=Configuration.PORT)
