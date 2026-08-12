import json
import uuid
from datetime import datetime

import pytest

from configuration import Configuration

pytestmark = pytest.mark.integration

BUY = {
    "name": "Ferrari F40",
    "categories": ["vehicles", "luxury"],
    "buying_price": 500000,
    "info": {"engine": {"power": 350}},
}


def stored_orders(orders):
    return {
        key.decode(): json.loads(value)
        for key, value in orders.hgetall(Configuration.REDIS_ORDERS).items()
    }


def only_order(orders):
    stored = stored_orders(orders)

    assert len(stored) == 1

    return next(iter(stored.items()))


def buy(client, headers, **overrides):
    return client.post("/create_buy_order", json={**BUY, **overrides}, headers=headers)


def sell(client, headers, **body):
    return client.post("/create_sell_order", json=body, headers=headers)


def decide(client, headers, **body):
    return client.post("/decision", json=body, headers=headers)


def insert_asset(assets, **overrides):
    asset = {
        "name": "Villa Gornji Milanovac",
        "categories": ["real estate"],
        "buying_price": 100000,
        "buying_date": datetime(2025, 1, 15, 9, 0, 0),
        "info": {"rooms": 12},
    }

    return assets.insert_one({**asset, **overrides}).inserted_id


# --- create_buy_order ------------------------------------------------------


def test_a_buy_order_lands_in_redis_under_a_fresh_uuid(employee_client, employee_headers, orders):
    response = buy(employee_client, employee_headers)

    assert response.status_code == 200
    assert response.data == b""

    key, order = only_order(orders)

    assert uuid.UUID(key)
    assert order == {"order_type": "BUY", **BUY}


def test_two_buy_orders_get_different_uuids(employee_client, employee_headers, orders):
    buy(employee_client, employee_headers)
    buy(employee_client, employee_headers, name="Zastava 101")

    assert len(stored_orders(orders)) == 2


@pytest.mark.parametrize("field", ["name", "categories", "buying_price", "info"])
def test_a_buy_order_reports_an_absent_field(employee_client, employee_headers, field):
    body = {name: value for name, value in BUY.items() if name != field}

    response = employee_client.post("/create_buy_order", json=body, headers=employee_headers)

    assert response.status_code == 400
    assert response.json == {"message": f"Field {field} is missing."}


@pytest.mark.parametrize("field", ["name", "categories", "buying_price", "info"])
def test_a_buy_order_reports_an_empty_string_field(employee_client, employee_headers, field):
    response = buy(employee_client, employee_headers, **{field: ""})

    assert response.json == {"message": f"Field {field} is missing."}


def test_a_buy_order_reports_the_first_absent_field_in_spec_order(
    employee_client, employee_headers
):
    response = employee_client.post("/create_buy_order", json={}, headers=employee_headers)

    assert response.json == {"message": "Field name is missing."}


def test_an_empty_categories_list_is_present_but_invalid(employee_client, employee_headers, orders):
    response = buy(employee_client, employee_headers, categories=[])

    assert response.status_code == 400
    assert response.json == {"message": "Categories list is empty."}
    assert stored_orders(orders) == {}


def test_the_empty_categories_list_is_reported_before_the_invalid_price(
    employee_client, employee_headers
):
    response = buy(employee_client, employee_headers, categories=[], buying_price=0)

    assert response.json == {"message": "Categories list is empty."}


@pytest.mark.parametrize("price", [0, -1, -0.5, "500000", True, None, [500000]])
def test_a_buy_order_rejects_a_price_that_is_not_a_positive_number(
    employee_client, employee_headers, price
):
    response = buy(employee_client, employee_headers, buying_price=price)

    assert response.status_code == 400
    assert response.json == {"message": "Invalid buying price."}


@pytest.mark.parametrize("price", [1, 0.5, 500000.75])
def test_a_buy_order_accepts_any_positive_number(employee_client, employee_headers, price):
    assert buy(employee_client, employee_headers, buying_price=price).status_code == 200


def test_an_empty_info_object_is_accepted(employee_client, employee_headers, orders):
    assert buy(employee_client, employee_headers, info={}).status_code == 200

    key, order = only_order(orders)

    assert order["info"] == {}


def test_create_buy_order_needs_an_employee_token(employee_client, director_headers):
    assert buy(employee_client, director_headers).status_code == 401
    assert employee_client.post("/create_buy_order", json=BUY).status_code == 401


# --- create_sell_order -----------------------------------------------------


def test_a_sell_order_lands_in_redis(employee_client, employee_headers, assets, orders):
    identifier = insert_asset(assets)

    response = sell(employee_client, employee_headers, id=str(identifier), selling_price=150000)

    assert response.status_code == 200
    assert response.data == b""

    key, order = only_order(orders)

    assert uuid.UUID(key)
    assert order == {"order_type": "SELL", "id": str(identifier), "selling_price": 150000}


@pytest.mark.parametrize("field", ["id", "selling_price"])
def test_a_sell_order_reports_an_absent_field(employee_client, employee_headers, assets, field):
    body = {"id": str(insert_asset(assets)), "selling_price": 150000}

    del body[field]

    response = employee_client.post("/create_sell_order", json=body, headers=employee_headers)

    assert response.json == {"message": f"Field {field} is missing."}


@pytest.mark.parametrize("identifier", ["nope", "6a7c6a95f20e416cdcb5c81", 12345, []])
def test_a_sell_order_rejects_a_malformed_id(employee_client, employee_headers, identifier):
    response = sell(employee_client, employee_headers, id=identifier, selling_price=150000)

    assert response.status_code == 400
    assert response.json == {"message": "Invalid id."}


def test_a_sell_order_rejects_a_well_formed_id_that_matches_no_asset(
    employee_client, employee_headers
):
    response = sell(
        employee_client, employee_headers, id="6a7c6a95f20e416cdcb5c818", selling_price=150000
    )

    assert response.json == {"message": "Invalid id."}


def test_the_invalid_id_is_reported_before_the_invalid_price(employee_client, employee_headers):
    response = sell(employee_client, employee_headers, id="nope", selling_price=0)

    assert response.json == {"message": "Invalid id."}


@pytest.mark.parametrize("price", [0, -1, "150000", True, None])
def test_a_sell_order_rejects_a_price_that_is_not_a_positive_number(
    employee_client, employee_headers, assets, price
):
    response = sell(
        employee_client, employee_headers, id=str(insert_asset(assets)), selling_price=price
    )

    assert response.json == {"message": "Invalid selling price."}


# --- pending_orders --------------------------------------------------------


def test_pending_orders_is_empty_when_nothing_waits(director_client, director_headers):
    response = director_client.get("/pending_orders", headers=director_headers)

    assert response.status_code == 200
    assert response.json == {"orders": []}


def test_pending_orders_shapes_both_order_types(
    employee_client, employee_headers, director_client, director_headers, assets
):
    identifier = insert_asset(assets)

    buy(employee_client, employee_headers)
    sell(employee_client, employee_headers, id=str(identifier), selling_price=150000)

    listed = director_client.get("/pending_orders", headers=director_headers).json["orders"]

    assert len(listed) == 2

    listed = {entry["order_type"]: entry for entry in listed}

    assert uuid.UUID(listed["BUY"].pop("uuid"))
    assert listed["BUY"] == {
        "order_type": "BUY",
        "name": "Ferrari F40",
        "categories": ["vehicles", "luxury"],
        "info": {"engine": {"power": 350}},
        "buying_price": 500000,
    }

    assert uuid.UUID(listed["SELL"].pop("uuid"))
    assert listed["SELL"] == {"order_type": "SELL", "id": str(identifier), "selling_price": 150000}


def test_pending_orders_needs_a_director_token(director_client, employee_headers):
    assert director_client.get("/pending_orders", headers=employee_headers).status_code == 401

    response = director_client.get("/pending_orders")

    assert response.status_code == 401
    assert response.json == {"msg": "Missing Authorization Header"}
