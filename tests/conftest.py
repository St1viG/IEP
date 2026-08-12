import pytest

from flask import Flask

from configuration import Configuration

from models import database


@pytest.fixture
def application ( ):
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

    application = Flask ( __name__ )
    application.config["SQLALCHEMY_DATABASE_URI"] = uri

    database.init_app ( application )

    with application.app_context ( ):
        database.drop_all ( )
        database.create_all ( )

        yield application

        database.session.remove ( )
        database.drop_all ( )
