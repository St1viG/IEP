import importlib

import pytest

from flask import Flask

from flask_jwt_extended import create_access_token

import configuration

from models import database
from models import Role


def build_headers ( application, roles, email = "onlymoney@gmail.com" ):
    claims = {
        "forename": "Scrooge",
        "surname":  "McDuck",
        "email":    email,
        "roles":    roles
    }

    with application.app_context ( ):
        token = create_access_token ( identity = email, additional_claims = claims )

    return { "Authorization": f"Bearer {token}" }


def testing_database_uri ( ):
    from sqlalchemy_utils import create_database
    from sqlalchemy_utils import database_exists

    uri = (
        f"mysql://{configuration.Configuration.DATABASE_USERNAME}:{configuration.Configuration.DATABASE_PASSWORD}"
        f"@{configuration.Configuration.DATABASE_URL}/{configuration.Configuration.DATABASE_NAME}_test"
    )

    try:
        if not database_exists ( uri ):
            create_database ( uri )
    except Exception as error:
        pytest.skip ( f"MySQL is not reachable, start development.yaml first: {error}" )

    return uri


@pytest.fixture
def application ( ):
    uri = testing_database_uri ( )

    application = Flask ( __name__ )
    application.config["SQLALCHEMY_DATABASE_URI"] = uri

    database.init_app ( application )

    with application.app_context ( ):
        database.drop_all ( )
        database.create_all ( )

        yield application

        database.session.remove ( )
        database.drop_all ( )


@pytest.fixture
def authentication_client ( monkeypatch ):
    uri = testing_database_uri ( )

    monkeypatch.setattr ( configuration.Configuration, "SQLALCHEMY_DATABASE_URI", uri )

    # Reloaded rather than imported once: the service reads the URI into a fresh
    # Flask application at import time, and flask_sqlalchemy refuses a second
    # init_app on an application it already knows.
    import authentication

    importlib.reload ( authentication )

    with authentication.application.app_context ( ):
        database.drop_all ( )
        database.create_all ( )

        database.session.add_all ( [ Role ( name = "director" ), Role ( name = "employee" ) ] )
        database.session.commit ( )

        yield authentication.application.test_client ( )

        database.session.remove ( )
        database.drop_all ( )


def require_mongo ( ):
    from pymongo import MongoClient

    probe = MongoClient (
        host                     = configuration.Configuration.MONGO_HOST,
        port                     = configuration.Configuration.MONGO_PORT,
        username                 = configuration.Configuration.MONGO_USERNAME,
        password                 = configuration.Configuration.MONGO_PASSWORD,
        authSource               = configuration.Configuration.MONGO_AUTH_SOURCE,
        serverSelectionTimeoutMS = 5000
    )

    try:
        probe.admin.command ( "ping" )
    except Exception as error:
        pytest.skip ( f"MongoDB is not reachable, start development.yaml first: {error}" )
    finally:
        probe.close ( )


def require_redis ( ):
    from redis import Redis

    probe = Redis (
        host            = configuration.Configuration.REDIS_HOST,
        port            = configuration.Configuration.REDIS_PORT,
        socket_timeout  = 5
    )

    try:
        probe.ping ( )
    except Exception as error:
        pytest.skip ( f"Redis is not reachable, start development.yaml first: {error}" )
    finally:
        probe.close ( )


@pytest.fixture
def fund_services ( monkeypatch ):
    """The employee and director services, bound to a test database and a test orders hash."""

    require_mongo ( )
    require_redis ( )

    monkeypatch.setattr ( configuration.Configuration, "MONGO_DATABASE", f"{configuration.Configuration.MONGO_DATABASE}_test" )
    monkeypatch.setattr ( configuration.Configuration, "REDIS_ORDERS", f"{configuration.Configuration.REDIS_ORDERS}_test" )

    import employee
    import director

    importlib.reload ( employee )
    importlib.reload ( director )

    def clear ( ):
        employee.assets.delete_many ( { } )
        employee.redis.delete ( configuration.Configuration.REDIS_ORDERS )

    clear ( )

    yield employee, director

    clear ( )

    employee.client.close ( )
    employee.redis.close ( )
    director.client.close ( )
    director.redis.close ( )


@pytest.fixture
def employee_service ( fund_services ):
    return fund_services[0]


@pytest.fixture
def director_service ( fund_services ):
    return fund_services[1]


@pytest.fixture
def employee_client ( employee_service ):
    return employee_service.application.test_client ( )


@pytest.fixture
def director_client ( director_service ):
    return director_service.application.test_client ( )


@pytest.fixture
def assets ( employee_service ):
    return employee_service.assets


@pytest.fixture
def orders ( employee_service ):
    return employee_service.redis


@pytest.fixture
def employee_headers ( employee_service ):
    return build_headers ( employee_service.application, [ "employee" ] )


@pytest.fixture
def director_headers ( director_service ):
    return build_headers ( director_service.application, [ "director" ] )
