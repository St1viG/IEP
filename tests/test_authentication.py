import pytest

from flask_jwt_extended import decode_token

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from models import Role
from models import User
from models import UserRole

pytestmark = pytest.mark.integration

SCROOGE = {
    "forename": "Scrooge",
    "surname":  "McDuck",
    "email":    "onlymoney@gmail.com",
    "password": "evenmoremoney"
}


def register ( client, **overrides ):
    return client.post ( "/register", json = { **SCROOGE, **overrides } )


def login ( client, **overrides ):
    body = { "email": SCROOGE["email"], "password": SCROOGE["password"] }

    return client.post ( "/login", json = { **body, **overrides } )


def access_token ( client ):
    return login ( client ).json["accessToken"]


def authorization ( token ):
    return { "Authorization": f"Bearer {token}" }


def test_register_creates_an_employee_and_answers_with_an_empty_body ( authentication_client ):
    response = register ( authentication_client )

    assert response.status_code == 200
    assert response.data == b""

    user = User.query.filter ( User.email == SCROOGE["email"] ).first ( )

    assert user.forename == "Scrooge"
    assert user.surname == "McDuck"
    assert [ role.name for role in user.roles ] == [ "employee" ]


def test_register_hashes_the_password ( authentication_client ):
    register ( authentication_client )

    user = User.query.filter ( User.email == SCROOGE["email"] ).first ( )

    assert user.password != SCROOGE["password"]
    assert check_password_hash ( user.password, SCROOGE["password"] )


@pytest.mark.parametrize ( "field", [ "forename", "surname", "email", "password" ] )
def test_register_reports_an_absent_field ( authentication_client, field ):
    body = { name: value for name, value in SCROOGE.items ( ) if name != field }

    response = authentication_client.post ( "/register", json = body )

    assert response.status_code == 400
    assert response.json == { "message": f"Field {field} is missing." }


@pytest.mark.parametrize ( "field", [ "forename", "surname", "email", "password" ] )
def test_register_reports_an_empty_field ( authentication_client, field ):
    response = register ( authentication_client, **{ field: "" } )

    assert response.status_code == 400
    assert response.json == { "message": f"Field {field} is missing." }


def test_register_reports_the_first_absent_field_in_spec_order ( authentication_client ):
    response = authentication_client.post ( "/register", json = { } )

    assert response.json == { "message": "Field forename is missing." }


def test_register_prefers_the_missing_field_over_the_invalid_email ( authentication_client ):
    response = authentication_client.post ( "/register", json = { "forename": "", "email": "bad" } )

    assert response.json == { "message": "Field forename is missing." }


def test_register_rejects_a_malformed_email ( authentication_client ):
    response = register ( authentication_client, email = "onlymoney" )

    assert response.status_code == 400
    assert response.json == { "message": "Invalid email." }


def test_register_prefers_the_invalid_email_over_the_short_password ( authentication_client ):
    response = register ( authentication_client, email = "onlymoney", password = "money" )

    assert response.json == { "message": "Invalid email." }


def test_register_rejects_a_password_shorter_than_eight_characters ( authentication_client ):
    response = register ( authentication_client, password = "money12" )

    assert response.status_code == 400
    assert response.json == { "message": "Invalid password." }


def test_register_accepts_a_password_of_exactly_eight_characters ( authentication_client ):
    assert register ( authentication_client, password = "money123" ).status_code == 200


def test_register_rejects_a_duplicate_email ( authentication_client ):
    register ( authentication_client )

    response = register ( authentication_client, forename = "Donald", surname = "Duck" )

    assert response.status_code == 400
    assert response.json == { "message": "Email already exists." }
    assert User.query.count ( ) == 1


def test_register_prefers_the_short_password_over_the_duplicate_email ( authentication_client ):
    register ( authentication_client )

    response = register ( authentication_client, password = "money" )

    assert response.json == { "message": "Invalid password." }


def test_login_answers_with_a_token_carrying_the_registration_claims ( authentication_client ):
    register ( authentication_client )

    response = login ( authentication_client )

    assert response.status_code == 200

    claims = decode_token ( response.json["accessToken"] )

    assert claims["sub"] == SCROOGE["email"]
    assert claims["forename"] == "Scrooge"
    assert claims["surname"] == "McDuck"
    assert claims["email"] == SCROOGE["email"]
    assert claims["roles"] == [ "employee" ]
    assert "password" not in claims


def test_the_token_is_valid_for_an_hour ( authentication_client ):
    register ( authentication_client )

    claims = decode_token ( access_token ( authentication_client ) )

    assert claims["exp"] - claims["iat"] == 3600


def test_login_carries_the_director_role_when_the_user_has_it ( authentication_client ):
    from models import database

    director = Role.query.filter ( Role.name == "director" ).first ( )

    user = User (
        forename = "Scrooge",
        surname  = "McDuck",
        email    = SCROOGE["email"],
        password = generate_password_hash ( SCROOGE["password"] )
    )

    user.roles.append ( director )

    database.session.add ( user )
    database.session.commit ( )

    claims = decode_token ( access_token ( authentication_client ) )

    assert claims["roles"] == [ "director" ]


@pytest.mark.parametrize ( "field", [ "email", "password" ] )
def test_login_reports_an_absent_field ( authentication_client, field ):
    body = { name: value for name, value in SCROOGE.items ( ) if name != field }

    response = authentication_client.post ( "/login", json = body )

    assert response.status_code == 400
    assert response.json == { "message": f"Field {field} is missing." }


def test_login_prefers_the_missing_password_over_the_invalid_email ( authentication_client ):
    response = authentication_client.post ( "/login", json = { "email": "onlymoney" } )

    assert response.json == { "message": "Field password is missing." }


def test_login_rejects_a_malformed_email ( authentication_client ):
    register ( authentication_client )

    response = login ( authentication_client, email = "onlymoney" )

    assert response.status_code == 400
    assert response.json == { "message": "Invalid email." }


def test_login_rejects_an_unknown_user ( authentication_client ):
    response = login ( authentication_client )

    assert response.status_code == 400
    assert response.json == { "message": "Invalid credentials." }


def test_login_rejects_a_wrong_password ( authentication_client ):
    register ( authentication_client )

    response = login ( authentication_client, password = "evenmoremone" )

    assert response.status_code == 400
    assert response.json == { "message": "Invalid credentials." }


def test_delete_without_a_header_answers_with_the_flask_jwt_extended_default ( authentication_client ):
    response = authentication_client.post ( "/delete" )

    assert response.status_code == 401
    assert response.json == { "msg": "Missing Authorization Header" }


def test_delete_removes_the_user_and_the_junction_row_but_keeps_the_roles ( authentication_client ):
    register ( authentication_client )

    response = authentication_client.post ( "/delete", headers = authorization ( access_token ( authentication_client ) ) )

    assert response.status_code == 200
    assert response.data == b""

    assert User.query.count ( ) == 0
    assert UserRole.query.count ( ) == 0
    assert sorted ( role.name for role in Role.query.all ( ) ) == [ "director", "employee" ]


def test_delete_reports_a_user_that_is_already_gone ( authentication_client ):
    register ( authentication_client )

    token = access_token ( authentication_client )

    authentication_client.post ( "/delete", headers = authorization ( token ) )

    response = authentication_client.post ( "/delete", headers = authorization ( token ) )

    assert response.status_code == 400
    assert response.json == { "message": "Unknown user." }


def test_a_deleted_email_can_register_again ( authentication_client ):
    register ( authentication_client )

    authentication_client.post ( "/delete", headers = authorization ( access_token ( authentication_client ) ) )

    assert register ( authentication_client ).status_code == 200
