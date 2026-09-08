from bson import ObjectId
from bson.json_util import dumps, loads
from flask import Flask, jsonify, request
from pymongo import MongoClient

application = Flask(__name__)

client = MongoClient(
    host="localhost", port=27017, username="root", password="example", authSource="admin"
)

database = client["course_shop"]


def parse_object_id(value: str):
    try:
        return ObjectId(value)
    except Exception:
        return None


def load_documents_from_request():
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return None, (
            jsonify({"error": "Attach a JSON file in form-data under the 'file' field"}),
            400,
        )

    try:
        raw_payload = upload.read().decode("utf-8")
        documents = loads(raw_payload)
    except Exception:
        return None, (jsonify({"error": "Uploaded file must contain valid JSON"}), 400)

    if isinstance(documents, dict):
        documents = [documents]

    if not isinstance(documents, list) or not documents:
        return None, (
            jsonify({"error": "Uploaded JSON must contain one document or a list of documents"}),
            400,
        )

    return documents, None


def import_documents(collection_name: str, documents: list):
    collection = database[collection_name]
    documents_with_ids = [doc for doc in documents if isinstance(doc, dict) and "_id" in doc]
    requested_ids = [doc["_id"] for doc in documents_with_ids]

    existing_ids = set()
    if requested_ids:
        existing_ids = {
            doc["_id"] for doc in collection.find({"_id": {"$in": requested_ids}}, {"_id": 1})
        }

    new_documents = [doc for doc in documents if "_id" not in doc or doc["_id"] not in existing_ids]

    inserted_count = 0
    if new_documents:
        inserted_count = len(collection.insert_many(new_documents).inserted_ids)

    return {
        "collection": collection_name,
        "inserted": inserted_count,
        "skipped": len(documents) - inserted_count,
        "total_in_file": len(documents),
    }


@application.route("/customers", methods=["GET"])
def get_customers():
    customers = list(database.customers.find())
    return dumps(customers), 200, {"Content-Type": "application/json"}


@application.route("/customers/import", methods=["POST"])
def import_customers():
    documents, error_response = load_documents_from_request()
    if error_response:
        return error_response

    result = import_documents("customers", documents)
    return jsonify(result), 201 if result["inserted"] else 200


@application.route("/products", methods=["GET"])
def get_products():
    category = request.args.get("category")

    query = {"category": category} if category else {}

    documents = list(database.products.find(query))
    return dumps(documents), 200, {"Content-Type": "application/json"}


@application.route("/products/import", methods=["POST"])
def import_products():
    documents, error_response = load_documents_from_request()
    if error_response:
        return error_response

    result = import_documents("products", documents)
    return jsonify(result), 201 if result["inserted"] else 200


@application.route("/orders", methods=["GET"])
def get_orders():
    documents = list(database.orders.find())
    return dumps(documents), 200, {"Content-Type": "application/json"}


@application.route("/orders/import", methods=["POST"])
def import_orders():
    documents, error_response = load_documents_from_request()
    if error_response:
        return error_response

    result = import_documents("orders", documents)
    return jsonify(result), 201 if result["inserted"] else 200


@application.route("/orders/<customer_id>", methods=["GET"])
def get_orders_for_customer(customer_id):
    oid = parse_object_id(customer_id)
    if not oid:
        return jsonify({"error": "Invalid customer_id"}), 400

    documents = list(database.orders.find({"customer_id": oid}))
    return dumps(documents), 200, {"Content-Type": "application/json"}


@application.route("/create_order", methods=["POST"])
def create_order():
    data = request.get_json(force=True)

    customer_id = parse_object_id(data.get("customer_id", ""))
    if not customer_id:
        return jsonify({"error": "Invalid or missing customer_id"}), 400

    items_input = data.get("items", [])
    if not items_input:
        return jsonify({"error": "Order must contain at least one item"}), 400

    order_items = []
    for raw_item in items_input:
        product_id = parse_object_id(raw_item.get("product_id", ""))
        quantity = int(raw_item.get("qty", 0))

        if not product_id or quantity <= 0:
            return jsonify({"error": "Each item needs valid product_id and qty > 0"}), 400

        product = database.products.find_one({"_id": product_id})
        if not product:
            return jsonify({"error": f"Product not found: {raw_item.get('product_id')}"}), 404

        order_items.append(
            {
                "product_id": product["_id"],
                "name": product["name"],
                "category": product["category"],
                "qty": quantity,
                "unit_price": product["price"],
            }
        )

    order_document = {
        "customer_id": customer_id,
        "created_at": data.get("created_at", {"$date": "2025-03-01T10:00:00Z"}),
        "status": data.get("status", "pending"),
        "items": order_items,
        "shipping": data.get("shipping", 5),
        "payment_method": data.get("payment_method", "card"),
    }

    result = database.orders.insert_one(order_document)
    return jsonify({"message": "Order created", "order_id": str(result.inserted_id)}), 201


@application.route("/reports/revenue-by-category", methods=["GET"])
def revenue_by_category():
    pipeline = [
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.category",
                "revenue": {"$sum": {"$multiply": ["$items.qty", "$items.unit_price"]}},
                "units": {"$sum": "$items.qty"},
            }
        },
        {"$sort": {"revenue": -1}},
    ]
    documents = list(database.orders.aggregate(pipeline))
    return dumps(documents), 200, {"Content-Type": "application/json"}


@application.route("/reports/top-customers", methods=["GET"])
def top_customers():
    pipeline = [
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$customer_id",
                "total_spent": {"$sum": {"$multiply": ["$items.qty", "$items.unit_price"]}},
            }
        },
        {
            "$lookup": {
                "from": "customers",
                "localField": "_id",
                "foreignField": "_id",
                "as": "customer",
            }
        },
        {"$unwind": "$customer"},
        {
            "$project": {
                "_id": 0,
                "customer_name": "$customer.name",
                "city": "$customer.city",
                "total_spent": 1,
            }
        },
        {"$sort": {"total_spent": -1}},
    ]
    documents = list(database.orders.aggregate(pipeline))
    return dumps(documents), 200, {"Content-Type": "application/json"}


if __name__ == "__main__":
    application.run(debug=True)
