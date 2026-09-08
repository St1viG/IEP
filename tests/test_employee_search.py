from datetime import datetime

import pytest

pytestmark = pytest.mark.integration

VILLA = {
    "name": "Villa Gornji Milanovac",
    "categories": ["real estate", "luxury"],
    "buying_price": 100000,
    "buying_date": datetime(2025, 1, 15, 9, 0, 0),
    "selling_price": 150000,
    "selling_date": datetime(2026, 3, 1, 12, 30, 0),
    "info": {"rooms": 12, "location": {"city": "Gornji Milanovac"}},
}

FERRARI = {
    "name": "Ferrari F.40",
    "categories": ["vehicles", "luxury"],
    "buying_price": 500000,
    "buying_date": datetime(2026, 2, 1, 8, 0, 0),
    "selling_price": 700000,
    "selling_date": datetime(2026, 6, 1, 18, 45, 0),
    "info": {"engine": {"power": 350, "fuel": "petrol"}},
}

ZASTAVA = {
    "name": "Zastava F140",
    "categories": ["vehicles"],
    "buying_price": 500,
    "buying_date": datetime(2026, 5, 1, 7, 15, 0),
    "info": {"engine": {"power": 40, "fuel": "petrol"}},
}


@pytest.fixture
def fund(assets):
    assets.insert_many([dict(VILLA), dict(FERRARI), dict(ZASTAVA)])

    return assets


def search(client, headers, **body):
    return client.post("/search", json=body, headers=headers)


def names(response):
    return sorted(asset["name"] for asset in response.json["assets"])


def test_an_empty_body_returns_every_asset(fund, employee_client, employee_headers):
    response = search(employee_client, employee_headers)

    assert response.status_code == 200
    assert names(response) == ["Ferrari F.40", "Villa Gornji Milanovac", "Zastava F140"]


def test_a_sold_asset_is_serialized_in_full(fund, employee_client, employee_headers):
    response = search(employee_client, employee_headers, name="Villa")

    asset = response.json["assets"][0]

    assert asset == {
        "id": str(fund.find_one({"name": VILLA["name"]})["_id"]),
        "name": "Villa Gornji Milanovac",
        "categories": ["real estate", "luxury"],
        "buying_price": 100000,
        "buying_date": "2025-01-15T09:00:00.000Z",
        "selling_price": 150000,
        "selling_date": "2026-03-01T12:30:00.000Z",
        "info": {"rooms": 12, "location": {"city": "Gornji Milanovac"}},
    }


def test_an_unsold_asset_omits_the_selling_fields(fund, employee_client, employee_headers):
    response = search(employee_client, employee_headers, name="Zastava")

    asset = response.json["assets"][0]

    assert "selling_price" not in asset
    assert "selling_date" not in asset
    assert asset["buying_date"] == "2026-05-01T07:15:00.000Z"


def test_name_matches_a_substring(fund, employee_client, employee_headers):
    assert names(search(employee_client, employee_headers, name="Gornji")) == [
        "Villa Gornji Milanovac"
    ]


def test_name_metacharacters_are_escaped(fund, employee_client, employee_headers):
    # An unescaped "F.40" would match "F140" as well.
    assert names(search(employee_client, employee_headers, name="F.40")) == ["Ferrari F.40"]


def test_name_that_matches_nothing_returns_an_empty_list(fund, employee_client, employee_headers):
    response = search(employee_client, employee_headers, name="Yacht")

    assert response.json == {"assets": []}


def test_category_matches_inside_the_array(fund, employee_client, employee_headers):
    assert names(search(employee_client, employee_headers, category="luxury")) == [
        "Ferrari F.40",
        "Villa Gornji Milanovac",
    ]
    assert names(search(employee_client, employee_headers, category="vehicles")) == [
        "Ferrari F.40",
        "Zastava F140",
    ]


def test_category_is_not_a_substring_match(fund, employee_client, employee_headers):
    assert names(search(employee_client, employee_headers, category="vehicle")) == []


def test_buying_date_keeps_only_later_purchases(fund, employee_client, employee_headers):
    response = search(employee_client, employee_headers, buying_date="2026-01-01T00:00:00.000Z")

    assert names(response) == ["Ferrari F.40", "Zastava F140"]


def test_buying_date_is_exclusive(fund, employee_client, employee_headers):
    response = search(employee_client, employee_headers, buying_date="2026-02-01T08:00:00.000Z")

    assert "Ferrari F.40" not in names(response)


def test_selling_date_keeps_only_earlier_sales_and_drops_unsold_assets(
    fund, employee_client, employee_headers
):
    response = search(employee_client, employee_headers, selling_date="2026-04-01T00:00:00.000Z")

    assert names(response) == ["Villa Gornji Milanovac"]


def test_selling_date_alone_excludes_every_unsold_asset(fund, employee_client, employee_headers):
    response = search(employee_client, employee_headers, selling_date="2030-01-01T00:00:00.000Z")

    assert names(response) == ["Ferrari F.40", "Villa Gornji Milanovac"]


def test_an_offset_is_understood_the_same_as_a_z_suffix(fund, employee_client, employee_headers):
    z = search(employee_client, employee_headers, buying_date="2026-02-01T08:00:00.000Z")
    offset = search(employee_client, employee_headers, buying_date="2026-02-01T10:00:00.000+02:00")

    assert names(z) == names(offset)


def test_a_nested_info_filter_compares_the_right_field(fund, employee_client, employee_headers):
    response = search(
        employee_client,
        employee_headers,
        info_filters=[{"field": "engine.power", "operator": "gt", "value": 100}],
    )

    assert names(response) == ["Ferrari F.40"]


def test_an_info_filter_on_a_string_field(fund, employee_client, employee_headers):
    response = search(
        employee_client,
        employee_headers,
        info_filters=[{"field": "location.city", "operator": "eq", "value": "Gornji Milanovac"}],
    )

    assert names(response) == ["Villa Gornji Milanovac"]


def test_two_filters_on_the_same_path_are_both_applied(fund, employee_client, employee_headers):
    response = search(
        employee_client,
        employee_headers,
        info_filters=[
            {"field": "engine.power", "operator": "gt", "value": 30},
            {"field": "engine.power", "operator": "lt", "value": 100},
        ],
    )

    assert names(response) == ["Zastava F140"]


def test_filters_of_every_kind_combine(fund, employee_client, employee_headers):
    response = search(
        employee_client,
        employee_headers,
        name="Ferrari",
        category="luxury",
        buying_date="2026-01-01T00:00:00.000Z",
        selling_date="2026-07-01T00:00:00.000Z",
        info_filters=[{"field": "engine.fuel", "operator": "eq", "value": "petrol"}],
    )

    assert names(response) == ["Ferrari F.40"]


def test_search_without_a_header_answers_with_the_flask_jwt_extended_default(fund, employee_client):
    response = employee_client.post("/search", json={})

    assert response.status_code == 401
    assert response.json == {"msg": "Missing Authorization Header"}


def test_a_director_token_cannot_search(fund, employee_client, director_headers):
    response = search(employee_client, director_headers)

    # Same answer as no token at all, see test_report.py for why.
    assert response.status_code == 401
    assert response.json == {"msg": "Missing Authorization Header"}
