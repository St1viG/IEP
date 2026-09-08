import os
from datetime import timedelta


class Configuration:
    HOST = "0.0.0.0" if ("PRODUCTION" in os.environ) else "localhost"

    DATABASE_URL = os.environ["DATABASE_URL"] if ("DATABASE_URL" in os.environ) else "localhost"
    DATABASE_USERNAME = (
        os.environ["DATABASE_USERNAME"] if ("DATABASE_USERNAME" in os.environ) else "root"
    )
    DATABASE_PASSWORD = (
        os.environ["DATABASE_PASSWORD"] if ("DATABASE_PASSWORD" in os.environ) else "root"
    )

    SQLALCHEMY_DATABASE_URI = (
        f"mysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}/users"
    )

    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    REDIS_HOST = os.environ["REDIS_HOST"] if ("REDIS_HOST" in os.environ) else "localhost"
    REDIS_PORT = int(os.environ["REDIS_PORT"]) if ("REDIS_PORT" in os.environ) else 6379
    REDIS_CHANNEL = os.environ["REDIS_CHANNEL"] if ("REDIS_CHANNEL" in os.environ) else "channel"
    REDIS_BUFFER = os.environ["REDIS_BUFFER"] if ("REDIS_BUFFER" in os.environ) else "banned"
