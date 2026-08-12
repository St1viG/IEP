from flask import Flask, Response, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from configuration import Configuration
from models import Role, User, database
from validation import missing_field, missing_field_message, valid_email

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)

jwt = JWTManager(application)


def error(message):
    return jsonify(message=message), 400


@application.route("/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}

    field = missing_field(body, ["forename", "surname", "email", "password"])

    if field is not None:
        return error(missing_field_message(field))

    if not valid_email(body["email"]):
        return error("Invalid email.")

    password = body["password"]

    if not isinstance(password, str) or len(password) < 8:
        return error("Invalid password.")

    if User.query.filter(User.email == body["email"]).first() is not None:
        return error("Email already exists.")

    user = User(
        forename=body["forename"],
        surname=body["surname"],
        email=body["email"],
        password=generate_password_hash(password),
    )

    user.roles.append(Role.query.filter(Role.name == "employee").first())

    database.session.add(user)
    database.session.commit()

    return Response(status=200)


@application.route("/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}

    field = missing_field(body, ["email", "password"])

    if field is not None:
        return error(missing_field_message(field))

    if not valid_email(body["email"]):
        return error("Invalid email.")

    password = body["password"]

    user = User.query.filter(User.email == body["email"]).first()

    if (
        user is None
        or not isinstance(password, str)
        or not check_password_hash(user.password, password)
    ):
        return error("Invalid credentials.")

    claims = {
        "forename": user.forename,
        "surname": user.surname,
        "email": user.email,
        "roles": [role.name for role in user.roles],
    }

    access_token = create_access_token(identity=user.email, additional_claims=claims)

    return jsonify(accessToken=access_token)


@application.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    user = User.query.filter(User.email == get_jwt_identity()).first()

    if user is None:
        return error("Unknown user.")

    database.session.delete(user)
    database.session.commit()

    return Response(status=200)


if __name__ == "__main__":
    application.run(debug=True, host=Configuration.HOST, port=Configuration.PORT)
