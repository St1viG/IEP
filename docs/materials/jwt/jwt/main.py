from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from configuration import Configuration
from models import Role, User, UserRole, database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)

with application.app_context():
    database.create_all()

    admin_role = Role.query.filter(Role.name == "admin").first()
    user_role = Role.query.filter(Role.name == "user").first()

    if admin_role is None:
        database.session.add(Role(name="admin"))

    if user_role is None:
        database.session.add(Role(name="user"))

    database.session.commit()


@application.route("/register", methods=["POST"])
def register():
    new_user = User(
        email=request.json["email"],
        password=request.json["password"],
        forename=request.json["forename"],
        surname=request.json["surname"],
    )
    database.session.add(new_user)
    database.session.commit()

    role_name = request.json["role_name"]

    role = Role.query.filter(Role.name == role_name).first()

    user_role = UserRole(user_id=new_user.id, role_id=role.id)

    database.session.add(user_role)
    database.session.commit()

    return "OK"


jwt = JWTManager(application)


@application.route("/login", methods=["POST"])
def login():
    email = request.json["email"]
    password = request.json["password"]

    user = User.query.filter(User.email == email, User.password == password).first()

    if not user:
        return "Invalid credentials", 401

    claims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [role.name for role in user.roles],
    }

    access_token = create_access_token(identity=user.email, additional_claims=claims)
    refresh_token = create_refresh_token(identity=user.email, additional_claims=claims)

    return jsonify(access_token=access_token, refresh_token=refresh_token)


@application.route("/check")
@jwt_required()
def check():
    identity = get_jwt_identity()
    claims = get_jwt()

    return f"IDENTITY: {identity}, CLAIMS: {claims}"


from decorators import role_check


@application.route("/user_check")
@role_check("user")
def user_check():
    identity = get_jwt_identity()
    claims = get_jwt()

    return f"IDENTITY: {identity}, CLAIMS: {claims}"


@application.route("/admin_check")
@role_check("admin")
def admin_check():
    identity = get_jwt_identity()
    claims = get_jwt()

    return f"IDENTITY: {identity}, CLAIMS: {claims}"


@application.route("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()

    return create_access_token(identity=identity, additional_claims=claims)


if __name__ == "__main__":
    application.run(host="0.0.0.0", debug=True)
