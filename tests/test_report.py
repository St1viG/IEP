from datetime import datetime

import pytest

pytestmark = pytest.mark.integration


def asset ( name, categories, buying_price, selling_price = None ):
    document = {
        "name":         name,
        "categories":   categories,
        "buying_price": buying_price,
        "buying_date":  datetime ( 2025, 1, 15, 9, 0, 0 ),
        "info":         { }
    }

    if selling_price is not None:
        document["selling_price"] = selling_price
        document["selling_date"]  = datetime ( 2026, 3, 1, 12, 30, 0 )

    return document


def statistics ( client, headers ):
    response = client.get ( "/report", headers = headers )

    assert response.status_code == 200

    return response.json["statistics"]


def test_a_fund_that_sold_nothing_reports_nothing ( assets, director_client, director_headers ):
    assets.insert_one ( asset ( "Zastava 101", [ "vehicles" ], 500 ) )

    assert statistics ( director_client, director_headers ) == [ ]


def test_an_empty_collection_reports_nothing ( director_client, director_headers ):
    assert statistics ( director_client, director_headers ) == [ ]


def test_a_sold_asset_is_summed_into_its_category ( assets, director_client, director_headers ):
    assets.insert_one ( asset ( "Villa", [ "real estate" ], 100000, 150000 ) )

    assert statistics ( director_client, director_headers ) == [
        { "category": "real estate", "spent": 100000, "earned": 150000 }
    ]


def test_an_asset_in_two_categories_counts_in_full_for_both ( assets, director_client, director_headers ):
    assets.insert_one ( asset ( "Ferrari F40", [ "vehicles", "luxury" ], 500000, 700000 ) )

    assert statistics ( director_client, director_headers ) == [
        { "category": "luxury",   "spent": 500000, "earned": 700000 },
        { "category": "vehicles", "spent": 500000, "earned": 700000 }
    ]


def test_prices_within_a_category_add_up ( assets, director_client, director_headers ):
    assets.insert_many ( [
        asset ( "Villa",   [ "real estate" ], 100000, 150000 ),
        asset ( "Cottage", [ "real estate" ],  20000,  25000 )
    ] )

    assert statistics ( director_client, director_headers ) == [
        { "category": "real estate", "spent": 120000, "earned": 175000 }
    ]


def test_an_unsold_asset_contributes_to_neither_column ( assets, director_client, director_headers ):
    assets.insert_many ( [
        asset ( "Villa",   [ "real estate" ], 100000, 150000 ),
        asset ( "Cottage", [ "real estate" ],  20000 )
    ] )

    # Reading A of the spec: the whole report covers sold assets only, so the
    # cottage's 20000 stays out of "spent" as well.
    assert statistics ( director_client, director_headers ) == [
        { "category": "real estate", "spent": 100000, "earned": 150000 }
    ]


def test_a_half_sold_asset_is_excluded ( assets, director_client, director_headers ):
    document = asset ( "Villa", [ "real estate" ], 100000, 150000 )

    del document["selling_date"]

    assets.insert_one ( document )

    assert statistics ( director_client, director_headers ) == [ ]


def test_the_three_sort_keys_are_applied_in_order ( assets, director_client, director_headers ):
    assets.insert_many ( [
        asset ( "A", [ "alpha" ],            100, 500 ),
        asset ( "B", [ "beta" ],             200, 500 ),
        asset ( "C", [ "gamma", "delta" ],    50,  50 ),
        asset ( "D", [ "alpha" ],            999 )
    ] )

    assert statistics ( director_client, director_headers ) == [
        # earned descending first
        { "category": "alpha", "spent": 100, "earned": 500 },
        { "category": "beta",  "spent": 200, "earned": 500 },   # ties on earned, loses on spent
        { "category": "delta", "spent":  50, "earned":  50 },
        { "category": "gamma", "spent":  50, "earned":  50 }    # ties on both, loses on name
    ]


def test_the_report_needs_a_director_token ( director_client, employee_headers ):
    assert director_client.get ( "/report", headers = employee_headers ).status_code == 401

    response = director_client.get ( "/report" )

    assert response.status_code == 401
    assert response.json == { "msg": "Missing Authorization Header" }
