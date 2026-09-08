from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from configuration import Configuration
from models import User, database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)

jwt = JWTManager(application)


@application.route("/login", methods=["POST"])
def login():
    username = request.json["username"]
    password = request.json["password"]

    user = User.query.filter(User.username == username, User.password == password).first()

    access_token = create_access_token(identity=user.username)

    return jsonify(access_token=access_token)


banned = []

from redis import Redis


def listener():
    with Redis(host=Configuration.REDIS_HOST, port=Configuration.REDIS_PORT, db=0) as redis:
        pubsub = redis.pubsub()
        pubsub.subscribe(Configuration.REDIS_CHANNEL)

        first = True
        for message in pubsub.listen():
            if first:
                first = False
                continue

            username = message["data"].decode()
            banned.append(username)


def banned_check(function):
    @jwt_required()
    def wrapper(*args, **kwargs):
        username = get_jwt_identity()
        if username not in banned:
            return function(*args, **kwargs)
        else:
            return "Invalid token"

    return wrapper


@application.route("/check")
@banned_check
def check():
    identity = get_jwt_identity()
    claims = get_jwt()

    return f"IDENTITY: {identity}, CLAIMS: {claims}"


import time
from threading import Thread

if __name__ == "__main__":
    done = False
    while not done:
        try:
            with Redis(host=Configuration.REDIS_HOST, port=Configuration.REDIS_PORT, db=0) as redis:
                list = redis.lrange(Configuration.REDIS_BUFFER, 0, -1)
                banned = [item.decode() for item in list]

            done = True
        except Exception:
            time.sleep(1)

    Thread(target=listener).start()

    application.run(host=Configuration.HOST, debug=True)
