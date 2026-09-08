import importlib

import pytest
from flask import Flask
from flask_jwt_extended import create_access_token

import configuration
from models import Role, database


def build_headers(application, roles, email="onlymoney@gmail.com"):
    claims = {"forename": "Scrooge", "surname": "McDuck", "email": email, "roles": roles}

    with application.app_context():
        token = create_access_token(identity=email, additional_claims=claims)

    return {"Authorization": f"Bearer {token}"}


# Probing once per service rather than once per test. Each probe costs a full
# connection timeout when the service is down, and there are 140 tests behind
# these gates, so without memoising, learning that development.yaml is not
# running takes nine minutes instead of five seconds.
_unreachable = {}


def _gate(name, probe):
    """Run `probe` once. Every later call re-raises the same skip immediately."""

    if name in _unreachable:
        pytest.skip(_unreachable[name])

    try:
        return probe()
    except Exception as error:
        _unreachable[name] = f"{name} is not reachable, start development.yaml first: {error}"

        pytest.skip(_unreachable[name])


def testing_database_uri():
    from sqlalchemy_utils import create_database, database_exists

    uri = (
        f"mysql://{configuration.Configuration.DATABASE_USERNAME}:{configuration.Configuration.DATABASE_PASSWORD}"
        f"@{configuration.Configuration.DATABASE_URL}/{configuration.Configuration.DATABASE_NAME}_test"
    )

    def probe():
        if not database_exists(uri):
            create_database(uri)

        return uri

    return _gate("MySQL", probe)


@pytest.fixture
def application():
    uri = testing_database_uri()

    application = Flask(__name__)
    application.config["SQLALCHEMY_DATABASE_URI"] = uri

    database.init_app(application)

    with application.app_context():
        database.drop_all()
        database.create_all()

        yield application

        database.session.remove()
        database.drop_all()


@pytest.fixture
def authentication_client(monkeypatch):
    uri = testing_database_uri()

    monkeypatch.setattr(configuration.Configuration, "SQLALCHEMY_DATABASE_URI", uri)

    # Reloaded rather than imported once: the service reads the URI into a fresh
    # Flask application at import time, and flask_sqlalchemy refuses a second
    # init_app on an application it already knows.
    import authentication

    importlib.reload(authentication)

    with authentication.application.app_context():
        database.drop_all()
        database.create_all()

        database.session.add_all([Role(name="director"), Role(name="employee")])
        database.session.commit()

        yield authentication.application.test_client()

        database.session.remove()
        database.drop_all()


def require_mongo():
    from pymongo import MongoClient

    probe = MongoClient(
        host=configuration.Configuration.MONGO_HOST,
        port=configuration.Configuration.MONGO_PORT,
        username=configuration.Configuration.MONGO_USERNAME,
        password=configuration.Configuration.MONGO_PASSWORD,
        authSource=configuration.Configuration.MONGO_AUTH_SOURCE,
        serverSelectionTimeoutMS=5000,
    )

    try:
        _gate("MongoDB", lambda: probe.admin.command("ping"))
    finally:
        probe.close()


def require_redis():
    from redis import Redis

    probe = Redis(
        host=configuration.Configuration.REDIS_HOST,
        port=configuration.Configuration.REDIS_PORT,
        socket_timeout=5,
    )

    try:
        _gate("Redis", probe.ping)
    finally:
        probe.close()


def require_ganache():
    from web3 import HTTPProvider, Web3

    web3 = Web3(
        HTTPProvider(configuration.Configuration.BLOCKCHAIN_URL, request_kwargs={"timeout": 10})
    )

    def probe():
        if not web3.is_connected():
            raise RuntimeError("no response")

        return web3

    return _gate("ganache", probe)


@pytest.fixture
def ganache():
    return require_ganache()


@pytest.fixture
def fund_services(monkeypatch):
    """The employee and director services, bound to a test database and a test orders hash."""

    require_mongo()
    require_redis()

    monkeypatch.setattr(
        configuration.Configuration,
        "MONGO_DATABASE",
        f"{configuration.Configuration.MONGO_DATABASE}_test",
    )
    monkeypatch.setattr(
        configuration.Configuration,
        "REDIS_ORDERS",
        f"{configuration.Configuration.REDIS_ORDERS}_test",
    )
    monkeypatch.setattr(
        configuration.Configuration,
        "REDIS_CONTRACTS",
        f"{configuration.Configuration.REDIS_CONTRACTS}_test",
    )

    import director
    import employee

    importlib.reload(employee)
    importlib.reload(director)

    def clear():
        employee.assets.delete_many({})
        employee.redis.delete(configuration.Configuration.REDIS_ORDERS)
        employee.redis.delete(configuration.Configuration.REDIS_CONTRACTS)

    clear()

    yield employee, director

    clear()

    employee.client.close()
    employee.redis.close()
    director.client.close()
    director.redis.close()


@pytest.fixture
def employee_service(fund_services):
    return fund_services[0]


@pytest.fixture
def director_service(fund_services):
    return fund_services[1]


@pytest.fixture
def employee_client(employee_service):
    return employee_service.application.test_client()


@pytest.fixture
def director_client(director_service):
    return director_service.application.test_client()


@pytest.fixture
def assets(employee_service):
    return employee_service.assets


@pytest.fixture
def orders(employee_service):
    return employee_service.redis


@pytest.fixture
def contracts(director_service):
    return director_service.redis


@pytest.fixture
def employee_headers(employee_service):
    return build_headers(employee_service.application, ["employee"])


@pytest.fixture
def director_headers(director_service):
    return build_headers(director_service.application, ["director"])
