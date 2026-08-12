import json
import uuid

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest

from configuration import Configuration

pytestmark = pytest.mark.integration

BUY = {
    "name":         "Ferrari F40",
    "categories":   [ "vehicles", "luxury" ],
    "buying_price": 500000,
    "info":         { "engine": { "power": 350 } }
}


def stored_orders ( orders ):
    return { key.decode ( ): json.loads ( value ) for key, value in orders.hgetall ( Configuration.REDIS_ORDERS ).items ( ) }


def only_order ( orders ):
    stored = stored_orders ( orders )

    assert len ( stored ) == 1

    return next ( iter ( stored.items ( ) ) )


def buy ( client, headers, **overrides ):
    return client.post ( "/create_buy_order", json = { **BUY, **overrides }, headers = headers )


def sell ( client, headers, **body ):
    return client.post ( "/create_sell_order", json = body, headers = headers )


def decide ( client, headers, **body ):
    return client.post ( "/decision", json = body, headers = headers )


def insert_asset ( assets, **overrides ):
    asset = {
        "name":         "Villa Gornji Milanovac",
        "categories":   [ "real estate" ],
        "buying_price": 100000,
        "buying_date":  datetime ( 2025, 1, 15, 9, 0, 0 ),
        "info":         { "rooms": 12 }
    }

    return assets.insert_one ( { **asset, **overrides } ).inserted_id


# --- create_buy_order ------------------------------------------------------


def test_a_buy_order_lands_in_redis_under_a_fresh_uuid ( employee_client, employee_headers, orders ):
    response = buy ( employee_client, employee_headers )

    assert response.status_code == 200
    assert response.data == b""

    key, order = only_order ( orders )

    assert uuid.UUID ( key )
    assert order == { "order_type": "BUY", **BUY }


def test_two_buy_orders_get_different_uuids ( employee_client, employee_headers, orders ):
    buy ( employee_client, employee_headers )
    buy ( employee_client, employee_headers, name = "Zastava 101" )

    assert len ( stored_orders ( orders ) ) == 2


@pytest.mark.parametrize ( "field", [ "name", "categories", "buying_price", "info" ] )
def test_a_buy_order_reports_an_absent_field ( employee_client, employee_headers, field ):
    body = { name: value for name, value in BUY.items ( ) if name != field }

    response = employee_client.post ( "/create_buy_order", json = body, headers = employee_headers )

    assert response.status_code == 400
    assert response.json == { "message": f"Field {field} is missing." }


@pytest.mark.parametrize ( "field", [ "name", "categories", "buying_price", "info" ] )
def test_a_buy_order_reports_an_empty_string_field ( employee_client, employee_headers, field ):
    response = buy ( employee_client, employee_headers, **{ field: "" } )

    assert response.json == { "message": f"Field {field} is missing." }


def test_a_buy_order_reports_the_first_absent_field_in_spec_order ( employee_client, employee_headers ):
    response = employee_client.post ( "/create_buy_order", json = { }, headers = employee_headers )

    assert response.json == { "message": "Field name is missing." }


def test_an_empty_categories_list_is_present_but_invalid ( employee_client, employee_headers, orders ):
    response = buy ( employee_client, employee_headers, categories = [ ] )

    assert response.status_code == 400
    assert response.json == { "message": "Categories list is empty." }
    assert stored_orders ( orders ) == { }


def test_the_empty_categories_list_is_reported_before_the_invalid_price ( employee_client, employee_headers ):
    response = buy ( employee_client, employee_headers, categories = [ ], buying_price = 0 )

    assert response.json == { "message": "Categories list is empty." }


@pytest.mark.parametrize ( "price", [ 0, -1, -0.5, "500000", True, None, [ 500000 ] ] )
def test_a_buy_order_rejects_a_price_that_is_not_a_positive_number ( employee_client, employee_headers, price ):
    response = buy ( employee_client, employee_headers, buying_price = price )

    assert response.status_code == 400
    assert response.json == { "message": "Invalid buying price." }


@pytest.mark.parametrize ( "price", [ 1, 0.5, 500000.75 ] )
def test_a_buy_order_accepts_any_positive_number ( employee_client, employee_headers, price ):
    assert buy ( employee_client, employee_headers, buying_price = price ).status_code == 200


def test_an_empty_info_object_is_accepted ( employee_client, employee_headers, orders ):
    assert buy ( employee_client, employee_headers, info = { } ).status_code == 200

    key, order = only_order ( orders )

    assert order["info"] == { }


def test_create_buy_order_needs_an_employee_token ( employee_client, director_headers ):
    assert buy ( employee_client, director_headers ).status_code == 401
    assert employee_client.post ( "/create_buy_order", json = BUY ).status_code == 401


# --- create_sell_order -----------------------------------------------------


def test_a_sell_order_lands_in_redis ( employee_client, employee_headers, assets, orders ):
    identifier = insert_asset ( assets )

    response = sell ( employee_client, employee_headers, id = str ( identifier ), selling_price = 150000 )

    assert response.status_code == 200
    assert response.data == b""

    key, order = only_order ( orders )

    assert uuid.UUID ( key )
    assert order == { "order_type": "SELL", "id": str ( identifier ), "selling_price": 150000 }


@pytest.mark.parametrize ( "field", [ "id", "selling_price" ] )
def test_a_sell_order_reports_an_absent_field ( employee_client, employee_headers, assets, field ):
    body = { "id": str ( insert_asset ( assets ) ), "selling_price": 150000 }

    del body[field]

    response = employee_client.post ( "/create_sell_order", json = body, headers = employee_headers )

    assert response.json == { "message": f"Field {field} is missing." }


@pytest.mark.parametrize ( "identifier", [ "nope", "6a7c6a95f20e416cdcb5c81", 12345, [ ] ] )
def test_a_sell_order_rejects_a_malformed_id ( employee_client, employee_headers, identifier ):
    response = sell ( employee_client, employee_headers, id = identifier, selling_price = 150000 )

    assert response.status_code == 400
    assert response.json == { "message": "Invalid id." }


def test_a_sell_order_rejects_a_well_formed_id_that_matches_no_asset ( employee_client, employee_headers ):
    response = sell ( employee_client, employee_headers, id = "6a7c6a95f20e416cdcb5c818", selling_price = 150000 )

    assert response.json == { "message": "Invalid id." }


def test_the_invalid_id_is_reported_before_the_invalid_price ( employee_client, employee_headers ):
    response = sell ( employee_client, employee_headers, id = "nope", selling_price = 0 )

    assert response.json == { "message": "Invalid id." }


@pytest.mark.parametrize ( "price", [ 0, -1, "150000", True, None ] )
def test_a_sell_order_rejects_a_price_that_is_not_a_positive_number ( employee_client, employee_headers, assets, price ):
    response = sell ( employee_client, employee_headers, id = str ( insert_asset ( assets ) ), selling_price = price )

    assert response.json == { "message": "Invalid selling price." }


# --- pending_orders --------------------------------------------------------


def test_pending_orders_is_empty_when_nothing_waits ( director_client, director_headers ):
    response = director_client.get ( "/pending_orders", headers = director_headers )

    assert response.status_code == 200
    assert response.json == { "orders": [ ] }


def test_pending_orders_shapes_both_order_types ( employee_client, employee_headers, director_client, director_headers, assets ):
    identifier = insert_asset ( assets )

    buy ( employee_client, employee_headers )
    sell ( employee_client, employee_headers, id = str ( identifier ), selling_price = 150000 )

    listed = director_client.get ( "/pending_orders", headers = director_headers ).json["orders"]

    assert len ( listed ) == 2

    listed = { entry["order_type"]: entry for entry in listed }

    assert uuid.UUID ( listed["BUY"].pop ( "uuid" ) )
    assert listed["BUY"] == {
        "order_type":   "BUY",
        "name":         "Ferrari F40",
        "categories":   [ "vehicles", "luxury" ],
        "info":         { "engine": { "power": 350 } },
        "buying_price": 500000
    }

    assert uuid.UUID ( listed["SELL"].pop ( "uuid" ) )
    assert listed["SELL"] == {
        "order_type":    "SELL",
        "id":            str ( identifier ),
        "selling_price": 150000
    }


def test_pending_orders_needs_a_director_token ( director_client, employee_headers ):
    assert director_client.get ( "/pending_orders", headers = employee_headers ).status_code == 401

    response = director_client.get ( "/pending_orders" )

    assert response.status_code == 401
    assert response.json == { "msg": "Missing Authorization Header" }


# --- decision --------------------------------------------------------------


def test_approving_a_buy_order_writes_the_asset_and_clears_redis ( employee_client, employee_headers, director_client, director_headers, assets, orders ):
    buy ( employee_client, employee_headers )

    order_uuid, _ = only_order ( orders )

    before   = datetime.now ( timezone.utc )
    response = decide ( director_client, director_headers, uuid = order_uuid, approved = True )
    after    = datetime.now ( timezone.utc )

    assert response.status_code == 200
    assert response.data == b""
    assert stored_orders ( orders ) == { }

    asset = assets.find_one ( { "name": "Ferrari F40" } )

    assert asset["categories"] == [ "vehicles", "luxury" ]
    assert asset["buying_price"] == 500000
    assert asset["info"] == { "engine": { "power": 350 } }
    assert "selling_price" not in asset
    assert "selling_date" not in asset

    # PyMongo hands the datetime back naive, in UTC.
    assert before <= asset["buying_date"].replace ( tzinfo = timezone.utc ) <= after


def test_the_buying_date_is_utc_not_local_time ( employee_client, employee_headers, director_client, director_headers, assets, orders ):
    buy ( employee_client, employee_headers )

    order_uuid, _ = only_order ( orders )

    decide ( director_client, director_headers, uuid = order_uuid, approved = True )

    # A naive datetime.now() on a UTC+2 machine would land half an hour past this bound.
    horizon = datetime.now ( timezone.utc ) + timedelta ( minutes = 30 )

    assert assets.count_documents ( { "buying_date": { "$gt": horizon } } ) == 0


def test_rejecting_a_buy_order_writes_nothing ( employee_client, employee_headers, director_client, director_headers, assets, orders ):
    buy ( employee_client, employee_headers )

    order_uuid, _ = only_order ( orders )

    response = decide ( director_client, director_headers, uuid = order_uuid, approved = False )

    assert response.status_code == 200
    assert stored_orders ( orders ) == { }
    assert assets.count_documents ( { } ) == 0


def test_approving_a_sell_order_updates_the_asset ( employee_client, employee_headers, director_client, director_headers, assets, orders ):
    identifier = insert_asset ( assets )

    sell ( employee_client, employee_headers, id = str ( identifier ), selling_price = 150000 )

    order_uuid, _ = only_order ( orders )

    before   = datetime.now ( timezone.utc )
    response = decide ( director_client, director_headers, uuid = order_uuid, approved = True )
    after    = datetime.now ( timezone.utc )

    assert response.status_code == 200
    assert stored_orders ( orders ) == { }

    asset = assets.find_one ( { "_id": identifier } )

    assert asset["selling_price"] == 150000
    assert before <= asset["selling_date"].replace ( tzinfo = timezone.utc ) <= after
    assert asset["buying_price"] == 100000
    assert assets.count_documents ( { } ) == 1


def test_rejecting_a_sell_order_leaves_the_asset_unsold ( employee_client, employee_headers, director_client, director_headers, assets, orders ):
    identifier = insert_asset ( assets )

    sell ( employee_client, employee_headers, id = str ( identifier ), selling_price = 150000 )

    order_uuid, _ = only_order ( orders )

    decide ( director_client, director_headers, uuid = order_uuid, approved = False )

    asset = assets.find_one ( { "_id": identifier } )

    assert stored_orders ( orders ) == { }
    assert "selling_price" not in asset
    assert "selling_date" not in asset


def test_a_decision_leaves_the_other_orders_alone ( employee_client, employee_headers, director_client, director_headers, orders ):
    buy ( employee_client, employee_headers )
    buy ( employee_client, employee_headers, name = "Zastava 101" )

    order_uuid = next ( iter ( stored_orders ( orders ) ) )

    decide ( director_client, director_headers, uuid = order_uuid, approved = False )

    assert len ( stored_orders ( orders ) ) == 1


@pytest.mark.parametrize ( "body", [ { }, { "approved": True }, { "uuid": "", "approved": True } ] )
def test_decision_reports_an_absent_uuid ( director_client, director_headers, body ):
    response = director_client.post ( "/decision", json = body, headers = director_headers )

    assert response.status_code == 400
    assert response.json == { "message": "Field uuid is missing." }


@pytest.mark.parametrize ( "value", [ "nope", "550e8400-e29b-41d4-a716", 12345, [ ] ] )
def test_decision_rejects_a_malformed_uuid ( director_client, director_headers, value ):
    response = director_client.post ( "/decision", json = { "uuid": value, "approved": True }, headers = director_headers )

    assert response.json == { "message": "Invalid uuid." }


def test_decision_rejects_a_well_formed_uuid_that_waits_for_nothing ( director_client, director_headers ):
    response = decide ( director_client, director_headers, uuid = str ( uuid.uuid4 ( ) ), approved = True )

    assert response.json == { "message": "Invalid uuid." }


def test_the_uuid_is_fully_validated_before_approved_is_looked_at ( director_client, director_headers ):
    response = director_client.post ( "/decision", json = { "uuid": "nope" }, headers = director_headers )

    assert response.json == { "message": "Invalid uuid." }


def test_decision_reports_an_absent_approved ( employee_client, employee_headers, director_client, director_headers, orders ):
    buy ( employee_client, employee_headers )

    order_uuid, _ = only_order ( orders )

    response = director_client.post ( "/decision", json = { "uuid": order_uuid }, headers = director_headers )

    assert response.status_code == 400
    assert response.json == { "message": "Field approved is missing." }


@pytest.mark.parametrize ( "value", [ "true", "True", "", 1, 0, None, [ True ] ] )
def test_decision_rejects_anything_that_is_not_a_real_boolean ( employee_client, employee_headers, director_client, director_headers, orders, assets, value ):
    buy ( employee_client, employee_headers )

    order_uuid, _ = only_order ( orders )

    response = decide ( director_client, director_headers, uuid = order_uuid, approved = value )

    assert response.status_code == 400
    assert response.json == { "message": "Invalid decision." }
    assert len ( stored_orders ( orders ) ) == 1
    assert assets.count_documents ( { } ) == 0


def test_decision_needs_a_director_token ( director_client, employee_headers ):
    assert decide ( director_client, employee_headers, uuid = str ( uuid.uuid4 ( ) ), approved = True ).status_code == 401

    response = director_client.post ( "/decision", json = { } )

    assert response.status_code == 401
    assert response.json == { "msg": "Missing Authorization Header" }
