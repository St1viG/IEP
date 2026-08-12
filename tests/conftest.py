import importlib

import pytest

from flask import Flask

from flask_jwt_extended import create_access_token

from configuration import Configuration

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
        f"mysql://{Configuration.DATABASE_USERNAME}:{Configuration.DATABASE_PASSWORD}"
        f"@{Configuration.DATABASE_URL}/{Configuration.DATABASE_NAME}_test"
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

    monkeypatch.setattr ( Configuration, "SQLALCHEMY_DATABASE_URI", uri )

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


@pytest.fixture
def employee_service ( monkeypatch ):
    from pymongo import MongoClient

    probe = MongoClient (
        host                     = Configuration.MONGO_HOST,
        port                     = Configuration.MONGO_PORT,
        username                 = Configuration.MONGO_USERNAME,
        password                 = Configuration.MONGO_PASSWORD,
        authSource               = Configuration.MONGO_AUTH_SOURCE,
        serverSelectionTimeoutMS = 5000
    )

    try:
        probe.admin.command ( "ping" )
    except Exception as error:
        pytest.skip ( f"MongoDB is not reachable, start development.yaml first: {error}" )
    finally:
        probe.close ( )

    monkeypatch.setattr ( Configuration, "MONGO_DATABASE", f"{Configuration.MONGO_DATABASE}_test" )

    import employee

    importlib.reload ( employee )

    employee.assets.delete_many ( { } )

    yield employee

    employee.assets.delete_many ( { } )


@pytest.fixture
def employee_client ( employee_service ):
    return employee_service.application.test_client ( )


@pytest.fixture
def assets ( employee_service ):
    return employee_service.assets


@pytest.fixture
def employee_headers ( employee_service ):
    return build_headers ( employee_service.application, [ "employee" ] )


@pytest.fixture
def director_headers ( employee_service ):
    return build_headers ( employee_service.application, [ "director" ] )
