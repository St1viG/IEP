from flask import Flask, jsonify, request
from sqlalchemy import func

from configuration import Configuration
from models import Employee, database

application = Flask(__name__)
application.config.from_object(Configuration)


@application.route("/", methods=["GET"])
def hello_world():
    return "<h1>Hello world!</h1>"


database.init_app(application)


@application.route("/add", methods=["POST"])
def add():
    new_employee = Employee(
        first_name=request.json["first_name"],
        last_name=request.json["last_name"],
        email=request.json["email"],
        gender=request.json["gender"],
        language=request.json["language"],
        position=request.json["position"],
    )

    database.session.add(new_employee)
    database.session.commit()

    return jsonify(employees=[str(employee) for employee in Employee.query.all()])


@application.route("/upload", methods=["POST"])
def upload():
    content = request.files["file"].stream.read().decode()

    for line in content.split("\n"):
        new_employee = Employee(*line.split(","))
        database.session.add(new_employee)

    database.session.commit()
    return jsonify(employees=[str(employee) for employee in Employee.query.all()])


@application.route("/search", methods=["GET"])
def search():
    criteria = ["first_name", "last_name", "email", "gender", "language", "position"]

    filters = []
    for criterium in criteria:
        if criterium in request.args:
            filters.append(getattr(Employee, criterium).like(f"%{request.args[criterium]}%"))

    result = Employee.query.filter(*filters)
    print(result)
    return jsonify(employees=[str(employee) for employee in result.all()])


@application.route("/statistics", methods=["GET"])
def statistics():
    result = (
        database.session.query(Employee.first_name, func.count("*"))
        .join(Employee.tasks)
        .group_by(Employee.id)
        .having(func.count("*") > 2)
    )

    print(result)
    return jsonify(result=[str(item) for item in result.all()])


import os

if __name__ == "__main__":
    database_created = False
    while not database_created:
        try:
            with application.app_context():
                database.create_all()

            database_created = True
        except Exception:
            pass

    HOST = "0.0.0.0" if ("PRODUCTION" in os.environ) else "127.0.0.1"
    application.run(debug=True, host=HOST)
