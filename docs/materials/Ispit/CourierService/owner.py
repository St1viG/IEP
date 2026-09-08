import datetime
import os

from flask import Flask, jsonify, request

from configuration import Configuration
from models import Courier, Package, database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(app=application)


@application.route("/add_package", methods=["POST"])
def add_package():
    description = request.json["description"]
    delivery_price = int(request.json["delivery_price"])
    arrival_date = datetime.datetime.now()

    new_package = Package(
        description=description, delivery_price=delivery_price, arrival_date=arrival_date
    )

    database.session.add(new_package)
    database.session.commit()

    return jsonify(id=new_package.id)


@application.route("/add_courier", methods=["POST"])
def add_courier():
    email = request.json["email"]
    forename = request.json["forename"]
    surname = request.json["surname"]

    new_courier = Courier(email=email, forename=forename, surname=surname)

    database.session.add(new_courier)
    database.session.commit()

    return jsonify(id=new_courier.id)


if __name__ == "__main__":
    PORT = os.environ["PORT"] if ("PORT" in os.environ) else "5000"
    HOST = "0.0.0.0" if ("PRODUCTION" in os.environ) else "localhost"

    application.run(debug=True, port=PORT, host=HOST)
