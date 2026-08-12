import pytest

from validation import missing_field
from validation import missing_field_message
from validation import valid_email


def test_nothing_missing_returns_none ( ):
    body = { "forename": "Scrooge", "surname": "McDuck", "email": "onlymoney@gmail.com", "password": "evenmoremoney" }

    assert missing_field ( body, [ "forename", "surname", "email", "password" ] ) is None


def test_absent_key_is_missing ( ):
    assert missing_field ( { "email": "onlymoney@gmail.com" }, [ "email", "password" ] ) == "password"


def test_empty_string_is_missing ( ):
    assert missing_field ( { "email": "" }, [ "email" ] ) == "email"


def test_the_list_order_decides_which_field_is_reported ( ):
    body = { }

    assert missing_field ( body, [ "email", "password" ] ) == "email"
    assert missing_field ( body, [ "password", "email" ] ) == "password"


@pytest.mark.parametrize ( "value", [ False, 0, 0.0, [ ], { }, None ] )
def test_falsy_values_that_are_present_are_not_missing ( value ):
    assert missing_field ( { "field": value }, [ "field" ] ) is None


def test_message_matches_the_spec_exactly ( ):
    assert missing_field_message ( "buying_price" ) == "Field buying_price is missing."


@pytest.mark.parametrize ( "value", [
    "onlymoney@gmail.com",
    "a@b.c",
    "first.last@sub.domain.rs"
] )
def test_valid_emails_are_accepted ( value ):
    assert valid_email ( value )


@pytest.mark.parametrize ( "value", [
    "",
    "onlymoney",
    "onlymoney@gmail",
    "@gmail.com",
    "onlymoney@.com",
    "only money@gmail.com",
    "onlymoney@gmail.com ",
    "two@at@gmail.com",
    None,
    12345
] )
def test_invalid_emails_are_rejected ( value ):
    assert not valid_email ( value )
