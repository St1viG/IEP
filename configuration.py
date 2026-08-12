import os
from datetime import timedelta


class Configuration:
    """Settings for every service, read from the environment.

    The defaults describe the stack in development.yaml running on the host, so a
    bare `python employee.py` works with no environment set. Compose and Kubernetes
    override each value with a service name.
    """

    HOST = "0.0.0.0" if "PRODUCTION" in os.environ else "localhost"

    DATABASE_USERNAME = os.environ.get("DATABASE_USERNAME", "root")
    DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "root")
    # Not "localhost": mysqlclient reads that as "use the unix socket" and never
    # opens a TCP connection, so it misses the container entirely.
    DATABASE_URL = os.environ.get("DATABASE_URL", "127.0.0.1")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "investment_fund")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}/{DATABASE_NAME}"
    )

    # Shared by all three services: a token issued by authentication has to verify
    # in employee and director, so they must agree on this value.
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "development-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
    MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))
    MONGO_USERNAME = os.environ.get("MONGO_USERNAME", "root")
    MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD", "example")
    MONGO_AUTH_SOURCE = os.environ.get("MONGO_AUTH_SOURCE", "admin")
    MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "investment_fund")
    MONGO_ASSETS = os.environ.get("MONGO_ASSETS", "assets")

    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
    REDIS_ORDERS = os.environ.get("REDIS_ORDERS", "orders")
    REDIS_CONTRACTS = os.environ.get("REDIS_CONTRACTS", "contracts")

    BLOCKCHAIN_URL = os.environ.get("BLOCKCHAIN_URL", "http://127.0.0.1:8545")

    PORT = int(os.environ.get("PORT", 5000))
