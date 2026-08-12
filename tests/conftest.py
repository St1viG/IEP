import importlib

import pytest

from flask import Flask

from configuration import Configuration

from models import database
from models import Role


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
