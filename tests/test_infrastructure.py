import pytest

from configuration import Configuration

pytestmark = pytest.mark.integration


def test_mysql_serves_the_configured_database ( ):
    import sqlalchemy

    engine = sqlalchemy.create_engine ( Configuration.SQLALCHEMY_DATABASE_URI )
    try:
        connection = engine.connect ( )
    except Exception as error:
        pytest.skip ( f"MySQL is not reachable, start development.yaml first: {error}" )

    with connection:
        schema = connection.execute ( sqlalchemy.text ( "select database()" ) ).scalar ( )

    assert schema == Configuration.DATABASE_NAME


def test_mongo_accepts_the_configured_credentials ( ):
    from pymongo import MongoClient

    client = MongoClient (
        host                     = Configuration.MONGO_HOST,
        port                     = Configuration.MONGO_PORT,
        username                 = Configuration.MONGO_USERNAME,
        password                 = Configuration.MONGO_PASSWORD,
        authSource               = Configuration.MONGO_AUTH_SOURCE,
        serverSelectionTimeoutMS = 5000
    )

    try:
        information = client.server_info ( )
    except Exception as error:
        pytest.skip ( f"MongoDB is not reachable, start development.yaml first: {error}" )

    assert information["ok"] == 1.0

    authenticated = client.admin.command ( "connectionStatus" )["authInfo"]["authenticatedUsers"]

    assert { "user": Configuration.MONGO_USERNAME, "db": Configuration.MONGO_AUTH_SOURCE } in authenticated


def test_redis_answers_a_ping ( ):
    from redis import Redis

    with Redis ( host = Configuration.REDIS_HOST, port = Configuration.REDIS_PORT, db = 0 ) as redis:
        try:
            assert redis.ping ( )
        except Exception as error:
            pytest.skip ( f"Redis is not reachable, start development.yaml first: {error}" )
