import importlib
import os

from datetime import timedelta

import configuration


def reload_with ( ** overrides ):
    previous = dict ( os.environ )
    os.environ.update ( overrides )
    try:
        return importlib.reload ( configuration ).Configuration
    finally:
        os.environ.clear ( )
        os.environ.update ( previous )
        importlib.reload ( configuration )


def test_defaults_target_the_development_stack ( ):
    Configuration = reload_with ( )

    assert Configuration.SQLALCHEMY_DATABASE_URI == "mysql://root:root@127.0.0.1/investment_fund"
    assert Configuration.MONGO_PORT == 27017
    assert Configuration.REDIS_PORT == 6379
    assert Configuration.HOST == "localhost"


def test_database_url_defaults_to_a_numeric_host ( ):
    Configuration = reload_with ( )

    assert Configuration.DATABASE_URL == "127.0.0.1"


def test_token_is_valid_for_one_hour ( ):
    Configuration = reload_with ( )

    assert Configuration.JWT_ACCESS_TOKEN_EXPIRES == timedelta ( hours = 1 )


def test_database_uri_is_built_from_the_environment ( ):
    Configuration = reload_with (
        DATABASE_USERNAME = "fund",
        DATABASE_PASSWORD = "secret",
        DATABASE_URL      = "mysql-service",
        DATABASE_NAME     = "production"
    )

    assert Configuration.SQLALCHEMY_DATABASE_URI == "mysql://fund:secret@mysql-service/production"


def test_ports_are_read_as_integers ( ):
    Configuration = reload_with ( MONGO_PORT = "27018", REDIS_PORT = "6380" )

    assert Configuration.MONGO_PORT == 27018
    assert Configuration.REDIS_PORT == 6380


def test_production_binds_every_interface ( ):
    Configuration = reload_with ( PRODUCTION = "1" )

    assert Configuration.HOST == "0.0.0.0"


def test_blockchain_url_is_keyed_off_its_own_variable ( ):
    Configuration = reload_with ( DATABASE_NAME = "production" )

    assert Configuration.BLOCKCHAIN_URL == "http://127.0.0.1:8545"
