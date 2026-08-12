import os

from datetime import timedelta


class Configuration:
    HOST = "0.0.0.0" if ( "PRODUCTION" in os.environ ) else "localhost"

    DATABASE_USERNAME = os.environ["DATABASE_USERNAME"] if ( "DATABASE_USERNAME" in os.environ ) else "root"
    DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"] if ( "DATABASE_PASSWORD" in os.environ ) else "root"
    DATABASE_URL      = os.environ["DATABASE_URL"]      if ( "DATABASE_URL"      in os.environ ) else "127.0.0.1"
    DATABASE_NAME     = os.environ["DATABASE_NAME"]     if ( "DATABASE_NAME"     in os.environ ) else "investment_fund"

    SQLALCHEMY_DATABASE_URI = f"mysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}/{DATABASE_NAME}"

    JWT_SECRET_KEY           = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta ( hours = 1 )

    MONGO_HOST        = os.environ["MONGO_HOST"]         if ( "MONGO_HOST"        in os.environ ) else "localhost"
    MONGO_PORT        = int ( os.environ["MONGO_PORT"] ) if ( "MONGO_PORT"        in os.environ ) else 27017
    MONGO_USERNAME    = os.environ["MONGO_USERNAME"]     if ( "MONGO_USERNAME"    in os.environ ) else "root"
    MONGO_PASSWORD    = os.environ["MONGO_PASSWORD"]     if ( "MONGO_PASSWORD"    in os.environ ) else "example"
    MONGO_AUTH_SOURCE = os.environ["MONGO_AUTH_SOURCE"]  if ( "MONGO_AUTH_SOURCE" in os.environ ) else "admin"
    MONGO_DATABASE    = os.environ["MONGO_DATABASE"]     if ( "MONGO_DATABASE"    in os.environ ) else "investment_fund"
    MONGO_ASSETS      = os.environ["MONGO_ASSETS"]       if ( "MONGO_ASSETS"      in os.environ ) else "assets"

    REDIS_HOST      = os.environ["REDIS_HOST"]         if ( "REDIS_HOST"      in os.environ ) else "localhost"
    REDIS_PORT      = int ( os.environ["REDIS_PORT"] ) if ( "REDIS_PORT"      in os.environ ) else 6379
    REDIS_ORDERS    = os.environ["REDIS_ORDERS"]       if ( "REDIS_ORDERS"    in os.environ ) else "orders"
    REDIS_CONTRACTS = os.environ["REDIS_CONTRACTS"]    if ( "REDIS_CONTRACTS" in os.environ ) else "contracts"

    BLOCKCHAIN_URL = os.environ["BLOCKCHAIN_URL"] if ( "BLOCKCHAIN_URL" in os.environ ) else "http://127.0.0.1:8545"
