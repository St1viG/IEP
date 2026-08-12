import json
import re
import uuid
from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, Response, jsonify, request
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from redis import Redis

from configuration import Configuration
from decorators import role_check
from validation import missing_field, missing_field_message, valid_price

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


def parse_iso(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def format_iso(value):
    return value.isoformat(timespec="milliseconds") + "Z"


def serialize(asset):
    serialized = {
        "id": str(asset["_id"]),
        "name": asset["name"],
        "categories": asset["categories"],
        "buying_price": asset["buying_price"],
        "buying_date": format_iso(asset["buying_date"]),
        "info": asset.get("info", {}),
    }

    if "selling_price" in asset:
        serialized["selling_price"] = asset["selling_price"]

    if "selling_date" in asset:
        serialized["selling_date"] = format_iso(asset["selling_date"])

    return serialized


@application.route("/search", methods=["POST"])
@role_check("employee")
def search():
    body = request.get_json(silent=True) or {}

    name = body.get("name")
    category = body.get("category")
    buying_date = body.get("buying_date")
    selling_date = body.get("selling_date")
    info_filters = body.get("info_filters") or []

    conditions = []

    if name is not None:
        conditions.append({"name": {"$regex": re.escape(name)}})

    if category is not None:
        conditions.append({"categories": category})

    if buying_date is not None:
        conditions.append({"buying_date": {"$gt": parse_iso(buying_date)}})

    if selling_date is not None:
        conditions.append({"selling_date": {"$lt": parse_iso(selling_date)}})

    for info_filter in info_filters:
        field = info_filter["field"]
        operator = info_filter["operator"]
        value = info_filter["value"]

        conditions.append({f"info.{field}": {f"${operator}": value}})

    query = {"$and": conditions} if (len(conditions) > 0) else {}

    return jsonify(assets=[serialize(asset) for asset in assets.find(query)])


@application.route("/create_buy_order", methods=["POST"])
@role_check("employee")
def create_buy_order():
    body = request.get_json(silent=True) or {}

    field = missing_field(body, ["name", "categories", "buying_price", "info"])

    if field is not None:
        return error(missing_field_message(field))

    categories = body["categories"]

    if not isinstance(categories, list) or len(categories) == 0:
        return error("Categories list is empty.")

    if not valid_price(body["buying_price"]):
        return error("Invalid buying price.")

    order = {
        "order_type": "BUY",
        "name": body["name"],
        "categories": categories,
        "buying_price": body["buying_price"],
        "info": body["info"],
    }

    redis.hset(Configuration.REDIS_ORDERS, str(uuid.uuid4()), json.dumps(order))

    return Response(status=200)


@application.route("/create_sell_order", methods=["POST"])
@role_check("employee")
def create_sell_order():
    body = request.get_json(silent=True) or {}

    field = missing_field(body, ["id", "selling_price"])

    if field is not None:
        return error(missing_field_message(field))

    try:
        identifier = ObjectId(body["id"])
    except (InvalidId, TypeError):
        return error("Invalid id.")

    if assets.find_one({"_id": identifier}, {"_id": 1}) is None:
        return error("Invalid id.")

    if not valid_price(body["selling_price"]):
        return error("Invalid selling price.")

    order = {"order_type": "SELL", "id": str(identifier), "selling_price": body["selling_price"]}

    redis.hset(Configuration.REDIS_ORDERS, str(uuid.uuid4()), json.dumps(order))

    return Response(status=200)


if __name__ == "__main__":
    application.run(debug=True, host=Configuration.HOST, port=Configuration.PORT)
