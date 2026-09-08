import os

DATABASE_USERNAME = (
    os.environ["DATABASE_USERNAME"] if ("DATABASE_USERNAME" in os.environ) else "root"
)
DATABASE_PASSWORD = (
    os.environ["DATABASE_PASSWORD"] if ("DATABASE_PASSWORD" in os.environ) else "root"
)
DATABASE_URL = os.environ["DATABASE_URL"] if ("DATABASE_URL" in os.environ) else "localhost"
DATABASE_NAME = (
    os.environ["DATABASE_NAME"] if ("DATABASE_NAME" in os.environ) else "courier_service_database"
)
BLOCKCHAIN_URL = (
    os.environ["BLOCKCHAIN_URL"] if ("DATABASE_NAME" in os.environ) else "http://127.0.0.1:8545"
)


class Configuration:
    SQLALCHEMY_DATABASE_URI = (
        f"mysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}/{DATABASE_NAME}"
    )
