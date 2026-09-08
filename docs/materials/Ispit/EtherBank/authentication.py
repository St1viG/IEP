import os

from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
)

from configuration import Configuration
from models import Role, User, UserRole, database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)

jwt = JWTManager(application)


@application.route("/register", methods=["POST"])
def register():
    new_user = User(
        email=request.json["email"],
        password=request.json["password"],
        account_address=request.json["account_address"],
    )
    database.session.add(new_user)
    database.session.commit()

    role = Role.query.filter(Role.name == "user").first()

    user_role = UserRole(user_id=new_user.id, role_id=role.id)

    database.session.add(user_role)
    database.session.commit()

    return jsonify(id=new_user.id)


@application.route("/login", methods=["POST"])
def login():
    email = request.json["email"]
    password = request.json["password"]

    user = User.query.filter(User.email == email, User.password == password).first()

    if not user:
        return ("Invalid credentials", 401)

    claims = {
        "id": user.id,
        "account_address": user.account_address,
        "roles": [role.name for role in user.roles],
    }

    access_token = create_access_token(identity=user.email, additional_claims=claims)

    return jsonify(access_token=access_token)


if __name__ == "__main__":
    PORT = os.environ["PORT"] if ("PORT" in os.environ) else "5000"
    HOST = "0.0.0.0" if ("PRODUCTION" in os.environ) else "localhost"

    application.run(debug=True, port=PORT, host=HOST)
