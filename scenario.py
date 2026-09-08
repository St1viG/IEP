import os
import time
import uuid

import requests
from web3 import HTTPProvider, Web3

AUTHENTICATION_URL = os.environ.get("AUTHENTICATION_URL", "http://localhost:5000")
EMPLOYEE_URL = os.environ.get("EMPLOYEE_URL", "http://localhost:5001")
DIRECTOR_URL = os.environ.get("DIRECTOR_URL", "http://localhost:5002")
BLOCKCHAIN_URL = os.environ.get("BLOCKCHAIN_URL", "http://127.0.0.1:8545")

web3 = Web3(HTTPProvider(BLOCKCHAIN_URL, request_kwargs={"timeout": 60}))

# Every run tags its own employee and assets, so a second run neither trips over
# the first run's leftovers nor needs the databases wiped between demos.
RUN = uuid.uuid4().hex[:8]

EMPLOYEE = {
    "forename": "Donald",
    "surname": "Duck",
    "email": f"donald-{RUN}@duck.com",
    "password": "quackquack",
}

FERRARI = f"Ferrari F40 {RUN}"
YACHT = f"Yacht {RUN}"

DIRECTOR = {"email": "onlymoney@gmail.com", "password": "evenmoremoney"}


def check(label, response, status=200, message=None):
    # role_check answers "Invalid role" as plain text, a body the spec never
    # describes, so not every response here is JSON.
    try:
        body = response.json()
    except ValueError:
        body = response.text

    if response.status_code != status or (message is not None and body["message"] != message):
        raise AssertionError(
            f"{label}: expected {status} {message}, got {response.status_code} {body}"
        )

    print(f"ok  {label}")

    return body


def authorization(token):
    return {"Authorization": f"Bearer {token}"}


def cast(transaction, sender):
    """Send one of the transactions /decision handed back, from a voter."""

    web3.eth.wait_for_transaction_receipt(
        web3.eth.send_transaction({**transaction, "from": sender})
    )


def settled(label, predicate, attempts=20):
    """Wait for the director's poller to notice the vote concluded."""

    for _ in range(attempts):
        if predicate():
            print(f"ok  {label}")
            return
        time.sleep(1)

    raise AssertionError(f"{label}: the poller never applied the outcome")


def search(token, **body):
    """A quiet /search, for polling and for assertions between the noisy steps."""

    response = requests.post(url=EMPLOYEE_URL + "/search", json=body, headers=authorization(token))

    assert response.status_code == 200, response.text

    return response.json()["assets"]


def wait_for_ganache(attempts=40):
    """The accounts, once the simulator will talk to us.

    The image the assignment mandates is amd64 only, so on an arm host it runs
    emulated and takes the better part of half a minute to accept its first
    connection. Reading the accounts straight away resets the connection and
    the script dies before printing a single line.
    """

    for remaining in range(attempts, 0, -1):
        try:
            return web3.eth.accounts
        except Exception:  # noqa: BLE001 - anything here means "not up yet"
            if remaining == 1:
                raise

            time.sleep(3)

    return []


VOTERS = wait_for_ganache()[1:4]


# --- accounts --------------------------------------------------------------

check("register the employee", requests.post(url=AUTHENTICATION_URL + "/register", json=EMPLOYEE))

check(
    "register the same email twice",
    requests.post(url=AUTHENTICATION_URL + "/register", json=EMPLOYEE),
    status=400,
    message="Email already exists.",
)

check(
    "register without a forename",
    requests.post(url=AUTHENTICATION_URL + "/register", json={**EMPLOYEE, "forename": ""}),
    status=400,
    message="Field forename is missing.",
)

employee_token = check(
    "log the employee in",
    requests.post(
        url=AUTHENTICATION_URL + "/login",
        json={"email": EMPLOYEE["email"], "password": EMPLOYEE["password"]},
    ),
)["accessToken"]

check(
    "log in with the wrong password",
    requests.post(
        url=AUTHENTICATION_URL + "/login", json={"email": EMPLOYEE["email"], "password": "quack"}
    ),
    status=400,
    message="Invalid credentials.",
)

director_token = check(
    "log the seeded director in", requests.post(url=AUTHENTICATION_URL + "/login", json=DIRECTOR)
)["accessToken"]

# --- a purchase, proposed and approved -------------------------------------

check(
    "search before anything is owned",
    requests.post(
        url=EMPLOYEE_URL + "/search",
        json={"name": FERRARI},
        headers=authorization(employee_token),
    ),
)

check("search without a token", requests.post(url=EMPLOYEE_URL + "/search", json={}), status=401)

check(
    "propose a purchase with an empty category list",
    requests.post(
        url=EMPLOYEE_URL + "/create_buy_order",
        json={"name": FERRARI, "categories": [], "buying_price": 500000, "info": {}},
        headers=authorization(employee_token),
    ),
    status=400,
    message="Categories list is empty.",
)

check(
    "propose a purchase",
    requests.post(
        url=EMPLOYEE_URL + "/create_buy_order",
        json={
            "name": FERRARI,
            "categories": ["vehicles", "luxury"],
            "buying_price": 500000,
            "info": {"engine": {"power": 350, "fuel": "petrol"}},
        },
        headers=authorization(employee_token),
    ),
)

orders = check(
    "list the pending orders",
    requests.get(url=DIRECTOR_URL + "/pending_orders", headers=authorization(director_token)),
)["orders"]

buy_order = [
    order for order in orders if (order["order_type"] == "BUY" and order["name"] == FERRARI)
][0]

check(
    "open a vote on something nobody proposed",
    requests.post(
        url=DIRECTOR_URL + "/decision",
        json={"uuid": "nope", "voters": VOTERS},
        headers=authorization(director_token),
    ),
    status=400,
    message="Invalid uuid.",
)

check(
    "open a vote with an even number of voters",
    requests.post(
        url=DIRECTOR_URL + "/decision",
        json={"uuid": buy_order["uuid"], "voters": VOTERS[:2]},
        headers=authorization(director_token),
    ),
    status=400,
    message="Even number of voters.",
)

check(
    "open a vote with a bad address",
    requests.post(
        url=DIRECTOR_URL + "/decision",
        json={"uuid": buy_order["uuid"], "voters": [*VOTERS, "not-an-address", VOTERS[0]]},
        headers=authorization(director_token),
    ),
    status=400,
    message="Invalid voter address.",
)

vote = check(
    "open the vote on the purchase",
    requests.post(
        url=DIRECTOR_URL + "/decision",
        json={"uuid": buy_order["uuid"], "voters": VOTERS},
        headers=authorization(director_token),
    ),
)

assert search(employee_token, name=FERRARI) == [], "nothing is bought before the vote concludes"

cast(vote["approve_transaction"], VOTERS[0])
print("ok  first voter approves")

assert search(employee_token, name=FERRARI) == [], "one of three votes is not a majority"

cast(vote["approve_transaction"], VOTERS[1])
print("ok  second voter approves, majority reached")

settled(
    "the director's poller books the purchase",
    lambda: len(search(employee_token, name=FERRARI)) == 1,
)

found = check(
    "find the freshly bought asset",
    requests.post(
        url=EMPLOYEE_URL + "/search",
        json={"name": FERRARI},
        headers=authorization(employee_token),
    ),
)["assets"]

assert len(found) == 1, found
assert "selling_price" not in found[0], found[0]

asset_id = found[0]["id"]

# --- a sale, proposed and approved -----------------------------------------

check(
    "propose a sale of an asset that does not exist",
    requests.post(
        url=EMPLOYEE_URL + "/create_sell_order",
        json={"id": "6a7c6a95f20e416cdcb5c818", "selling_price": 700000},
        headers=authorization(employee_token),
    ),
    status=400,
    message="Invalid id.",
)

check(
    "propose a sale",
    requests.post(
        url=EMPLOYEE_URL + "/create_sell_order",
        json={"id": asset_id, "selling_price": 700000},
        headers=authorization(employee_token),
    ),
)

orders = check(
    "list the pending orders again",
    requests.get(url=DIRECTOR_URL + "/pending_orders", headers=authorization(director_token)),
)["orders"]

sell_order = [
    order for order in orders if (order["order_type"] == "SELL" and order["id"] == asset_id)
][0]

vote = check(
    "open the vote on the sale",
    requests.post(
        url=DIRECTOR_URL + "/decision",
        json={"uuid": sell_order["uuid"], "voters": VOTERS},
        headers=authorization(director_token),
    ),
)

cast(vote["approve_transaction"], VOTERS[1])
cast(vote["approve_transaction"], VOTERS[2])
print("ok  two of three voters approve the sale")

settled(
    "the director's poller books the sale",
    lambda: search(employee_token, name=FERRARI)[0].get("selling_price") == 700000,
)

sold = check(
    "find the asset among the sold ones",
    requests.post(
        url=EMPLOYEE_URL + "/search",
        json={
            # Name included so a previous run's Ferrari, which also matches the
            # date and the info filter, stays out of this assertion.
            "name": FERRARI,
            "selling_date": "2100-01-01T00:00:00.000Z",
            "info_filters": [{"field": "engine.power", "operator": "gt", "value": 300}],
        },
        headers=authorization(employee_token),
    ),
)["assets"]

assert [asset["id"] for asset in sold] == [asset_id], sold
assert sold[0]["selling_price"] == 700000, sold[0]

# --- and it shows up in the report -----------------------------------------

check(
    "read the report with an employee token",
    requests.get(url=DIRECTOR_URL + "/report", headers=authorization(employee_token)),
    status=401,
)

statistics = check(
    "read the report",
    requests.get(url=DIRECTOR_URL + "/report", headers=authorization(director_token)),
)["statistics"]

for category in ["vehicles", "luxury"]:
    row = [entry for entry in statistics if (entry["category"] == category)][0]

    assert row["spent"] >= 500000, row
    assert row["earned"] >= 700000, row

# Holds whatever else the fund already owned: earned descending, then spent
# ascending, then category ascending.
sort_keys = [(-entry["earned"], entry["spent"], entry["category"]) for entry in statistics]

assert sort_keys == sorted(sort_keys), statistics

# --- a rejected proposal leaves no trace -----------------------------------

check(
    "propose a purchase that will be rejected",
    requests.post(
        url=EMPLOYEE_URL + "/create_buy_order",
        json={"name": YACHT, "categories": ["luxury"], "buying_price": 1000000, "info": {}},
        headers=authorization(employee_token),
    ),
)

orders = check(
    "list the pending orders once more",
    requests.get(url=DIRECTOR_URL + "/pending_orders", headers=authorization(director_token)),
)["orders"]

yacht = [order for order in orders if (order["order_type"] == "BUY" and order["name"] == YACHT)][0]

vote = check(
    "open the vote on the yacht",
    requests.post(
        url=DIRECTOR_URL + "/decision",
        json={"uuid": yacht["uuid"], "voters": VOTERS},
        headers=authorization(director_token),
    ),
)

cast(vote["reject_transaction"], VOTERS[0])
cast(vote["reject_transaction"], VOTERS[2])
print("ok  two of three voters reject the yacht")

settled(
    "the rejected order disappears",
    lambda: (
        [
            order
            for order in requests.get(
                url=DIRECTOR_URL + "/pending_orders", headers=authorization(director_token)
            ).json()["orders"]
            if order["uuid"] == yacht["uuid"]
        ]
        == []
    ),
)

orders = check(
    "the rejected order is gone",
    requests.get(url=DIRECTOR_URL + "/pending_orders", headers=authorization(director_token)),
)["orders"]

assert [order for order in orders if (order["uuid"] == yacht["uuid"])] == [], orders

found = check(
    "and it bought nothing",
    requests.post(
        url=EMPLOYEE_URL + "/search", json={"name": YACHT}, headers=authorization(employee_token)
    ),
)["assets"]

assert found == [], found

# --- and the employee leaves -----------------------------------------------

check(
    "delete the employee account",
    requests.post(url=AUTHENTICATION_URL + "/delete", headers=authorization(employee_token)),
)

check(
    "delete it a second time",
    requests.post(url=AUTHENTICATION_URL + "/delete", headers=authorization(employee_token)),
    status=400,
    message="Unknown user.",
)

print("\nscenario passed")
