from flask import Flask
from redis import Redis

from configuration import Configuration
from models import User, database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)


def update(username):
    with Redis(host=Configuration.REDIS_HOST, port=Configuration.REDIS_PORT, db=0) as redis:
        redis.lpush(Configuration.REDIS_BUFFER, username)
        redis.publish(Configuration.REDIS_CHANNEL, username)


@application.route("/delete/<int:id>", methods=["GET"])
def delete(id):
    user = User.query.filter(User.id == id).first()

    username = user.username

    database.session.delete(user)
    database.session.commit()

    update(username)

    return "OK"


if __name__ == "__main__":
    application.run(host=Configuration.HOST, debug=True)
