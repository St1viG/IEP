import os

import requests

AUTHENTICATION_URL = os.environ["AUTHENTICATION_URL"] if ( "AUTHENTICATION_URL" in os.environ ) else "http://localhost:5000"
EMPLOYEE_URL       = os.environ["EMPLOYEE_URL"]       if ( "EMPLOYEE_URL"       in os.environ ) else "http://localhost:5001"
DIRECTOR_URL       = os.environ["DIRECTOR_URL"]       if ( "DIRECTOR_URL"       in os.environ ) else "http://localhost:5002"

EMPLOYEE = {
    "forename": "Donald",
    "surname":  "Duck",
    "email":    "donald@duck.com",
    "password": "quackquack"
}

DIRECTOR = {
    "email":    "onlymoney@gmail.com",
    "password": "evenmoremoney"
}


def check ( label, response, status = 200, message = None ):
    # role_check answers "Invalid role" as plain text, a body the spec never
    # describes, so not every response here is JSON.
    try:
        body = response.json ( )
    except ValueError:
        body = response.text

    if ( response.status_code != status or ( message is not None and body["message"] != message ) ):
        raise AssertionError ( f"{label}: expected {status} {message}, got {response.status_code} {body}" )

    print ( f"ok  {label}" )

    return body


def authorization ( token ):
    return { "Authorization": f"Bearer {token}" }


# --- accounts --------------------------------------------------------------

check (
    "register the employee",
    requests.post ( url = AUTHENTICATION_URL + "/register", json = EMPLOYEE )
)

check (
    "register the same email twice",
    requests.post ( url = AUTHENTICATION_URL + "/register", json = EMPLOYEE ),
    status  = 400,
    message = "Email already exists."
)

check (
    "register without a forename",
    requests.post ( url = AUTHENTICATION_URL + "/register", json = { **EMPLOYEE, "forename": "" } ),
    status  = 400,
    message = "Field forename is missing."
)

employee_token = check (
    "log the employee in",
    requests.post ( url = AUTHENTICATION_URL + "/login", json = { "email": EMPLOYEE["email"], "password": EMPLOYEE["password"] } )
)["accessToken"]

check (
    "log in with the wrong password",
    requests.post ( url = AUTHENTICATION_URL + "/login", json = { "email": EMPLOYEE["email"], "password": "quack" } ),
    status  = 400,
    message = "Invalid credentials."
)

director_token = check (
    "log the seeded director in",
    requests.post ( url = AUTHENTICATION_URL + "/login", json = DIRECTOR )
)["accessToken"]

# --- a purchase, proposed and approved -------------------------------------

check (
    "search before anything is owned",
    requests.post ( url = EMPLOYEE_URL + "/search", json = { "name": "Ferrari" }, headers = authorization ( employee_token ) )
)

check (
    "search without a token",
    requests.post ( url = EMPLOYEE_URL + "/search", json = { } ),
    status = 401
)

check (
    "propose a purchase with an empty category list",
    requests.post (
        url     = EMPLOYEE_URL + "/create_buy_order",
        json    = { "name": "Ferrari F40", "categories": [ ], "buying_price": 500000, "info": { } },
        headers = authorization ( employee_token )
    ),
    status  = 400,
    message = "Categories list is empty."
)

check (
    "propose a purchase",
    requests.post (
        url  = EMPLOYEE_URL + "/create_buy_order",
        json = {
            "name":         "Ferrari F40",
            "categories":   [ "vehicles", "luxury" ],
            "buying_price": 500000,
            "info":         { "engine": { "power": 350, "fuel": "petrol" } }
        },
        headers = authorization ( employee_token )
    )
)

orders = check (
    "list the pending orders",
    requests.get ( url = DIRECTOR_URL + "/pending_orders", headers = authorization ( director_token ) )
)["orders"]

buy_order = [ order for order in orders if ( order["order_type"] == "BUY" and order["name"] == "Ferrari F40" ) ][0]

check (
    "approve a decision that nobody proposed",
    requests.post (
        url     = DIRECTOR_URL + "/decision",
        json    = { "uuid": "nope", "approved": True },
        headers = authorization ( director_token )
    ),
    status  = 400,
    message = "Invalid uuid."
)

check (
    "approve the purchase",
    requests.post (
        url     = DIRECTOR_URL + "/decision",
        json    = { "uuid": buy_order["uuid"], "approved": True },
        headers = authorization ( director_token )
    )
)

found = check (
    "find the freshly bought asset",
    requests.post ( url = EMPLOYEE_URL + "/search", json = { "name": "Ferrari" }, headers = authorization ( employee_token ) )
)["assets"]

assert len ( found ) == 1, found
assert "selling_price" not in found[0], found[0]

asset_id = found[0]["id"]

# --- a sale, proposed and approved -----------------------------------------

check (
    "propose a sale of an asset that does not exist",
    requests.post (
        url     = EMPLOYEE_URL + "/create_sell_order",
        json    = { "id": "6a7c6a95f20e416cdcb5c818", "selling_price": 700000 },
        headers = authorization ( employee_token )
    ),
    status  = 400,
    message = "Invalid id."
)

check (
    "propose a sale",
    requests.post (
        url     = EMPLOYEE_URL + "/create_sell_order",
        json    = { "id": asset_id, "selling_price": 700000 },
        headers = authorization ( employee_token )
    )
)

orders = check (
    "list the pending orders again",
    requests.get ( url = DIRECTOR_URL + "/pending_orders", headers = authorization ( director_token ) )
)["orders"]

sell_order = [ order for order in orders if ( order["order_type"] == "SELL" and order["id"] == asset_id ) ][0]

check (
    "approve the sale",
    requests.post (
        url     = DIRECTOR_URL + "/decision",
        json    = { "uuid": sell_order["uuid"], "approved": True },
        headers = authorization ( director_token )
    )
)

sold = check (
    "find the asset among the sold ones",
    requests.post (
        url     = EMPLOYEE_URL + "/search",
        json    = { "selling_date": "2100-01-01T00:00:00.000Z", "info_filters": [ { "field": "engine.power", "operator": "gt", "value": 300 } ] },
        headers = authorization ( employee_token )
    )
)["assets"]

assert [ asset["id"] for asset in sold ] == [ asset_id ], sold
assert sold[0]["selling_price"] == 700000, sold[0]

# --- and it shows up in the report -----------------------------------------

check (
    "read the report with an employee token",
    requests.get ( url = DIRECTOR_URL + "/report", headers = authorization ( employee_token ) ),
    status = 401
)

statistics = check (
    "read the report",
    requests.get ( url = DIRECTOR_URL + "/report", headers = authorization ( director_token ) )
)["statistics"]

for category in [ "vehicles", "luxury" ]:
    row = [ entry for entry in statistics if ( entry["category"] == category ) ][0]

    assert row["spent"] >= 500000, row
    assert row["earned"] >= 700000, row

# Holds whatever else the fund already owned: earned descending, then spent
# ascending, then category ascending.
sort_keys = [ ( - entry["earned"], entry["spent"], entry["category"] ) for entry in statistics ]

assert sort_keys == sorted ( sort_keys ), statistics

# --- a rejected proposal leaves no trace -----------------------------------

check (
    "propose a purchase that will be rejected",
    requests.post (
        url     = EMPLOYEE_URL + "/create_buy_order",
        json    = { "name": "Yacht", "categories": [ "luxury" ], "buying_price": 1000000, "info": { } },
        headers = authorization ( employee_token )
    )
)

orders = check (
    "list the pending orders once more",
    requests.get ( url = DIRECTOR_URL + "/pending_orders", headers = authorization ( director_token ) )
)["orders"]

yacht = [ order for order in orders if ( order["order_type"] == "BUY" and order["name"] == "Yacht" ) ][0]

check (
    "reject the purchase",
    requests.post (
        url     = DIRECTOR_URL + "/decision",
        json    = { "uuid": yacht["uuid"], "approved": False },
        headers = authorization ( director_token )
    )
)

orders = check (
    "the rejected order is gone",
    requests.get ( url = DIRECTOR_URL + "/pending_orders", headers = authorization ( director_token ) )
)["orders"]

assert [ order for order in orders if ( order["uuid"] == yacht["uuid"] ) ] == [ ], orders

found = check (
    "and it bought nothing",
    requests.post ( url = EMPLOYEE_URL + "/search", json = { "name": "Yacht" }, headers = authorization ( employee_token ) )
)["assets"]

assert found == [ ], found

# --- and the employee leaves -----------------------------------------------

check (
    "delete the employee account",
    requests.post ( url = AUTHENTICATION_URL + "/delete", headers = authorization ( employee_token ) )
)

check (
    "delete it a second time",
    requests.post ( url = AUTHENTICATION_URL + "/delete", headers = authorization ( employee_token ) ),
    status  = 400,
    message = "Unknown user."
)

print ( "\nscenario passed" )
