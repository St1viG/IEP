import json
import uuid
from datetime import UTC, datetime

import pytest

from configuration import Configuration

pytestmark = pytest.mark.integration

BUY = {
    "name": "Ferrari F40",
    "categories": ["vehicles", "luxury"],
    "buying_price": 500000,
    "info": {"engine": {"power": 350}},
}


def propose_buy(client, headers, **overrides):
    return client.post("/create_buy_order", json={**BUY, **overrides}, headers=headers)


def only_uuid(orders):
    stored = orders.hgetall(Configuration.REDIS_ORDERS)

    assert len(stored) == 1

    return next(iter(stored)).decode()


def decide(client, headers, **body):
    return client.post("/decision", json=body, headers=headers)


def pending(orders):
    return {key.decode() for key in orders.hgetall(Configuration.REDIS_ORDERS)}


def live_contracts(contracts):
    return {
        key.decode(): value.decode()
        for key, value in contracts.hgetall(Configuration.REDIS_CONTRACTS).items()
    }


@pytest.fixture
def waiting_order(employee_client, employee_headers, orders):
    """A buy order sitting in Redis, waiting on a decision."""

    propose_buy(employee_client, employee_headers)

    return only_uuid(orders)


@pytest.fixture
def voters(ganache):
    return ganache.eth.accounts[1:4]


# --- validation, in the spec's order ---------------------------------------


@pytest.mark.parametrize("body", [{}, {"voters": []}, {"uuid": ""}])
def test_an_absent_uuid_is_reported_first(director_client, director_headers, body):
    response = director_client.post("/decision", json=body, headers=director_headers)

    assert response.status_code == 400
    assert response.json == {"message": "Field uuid is missing."}


@pytest.mark.parametrize("value", ["nope", "550e8400-e29b-41d4-a716", 12345, []])
def test_a_malformed_uuid_is_rejected(director_client, director_headers, value):
    response = director_client.post(
        "/decision", json={"uuid": value, "voters": []}, headers=director_headers
    )

    assert response.json == {"message": "Invalid uuid."}


def test_a_uuid_that_waits_for_nothing_is_rejected(director_client, director_headers):
    response = decide(director_client, director_headers, uuid=str(uuid.uuid4()), voters=[])

    assert response.json == {"message": "Invalid uuid."}


def test_the_uuid_is_fully_validated_before_the_voters_are(director_client, director_headers):
    # Both fields are wrong; the uuid owns the message.
    response = decide(director_client, director_headers, uuid="nope", voters=["not-an-address"])

    assert response.json == {"message": "Invalid uuid."}


@pytest.mark.parametrize("value", [None, [], "0x0", 5])
def test_absent_or_empty_voters_are_reported(
    director_client, director_headers, waiting_order, value
):
    body = {"uuid": waiting_order}

    if value is not None:
        body["voters"] = value

    response = director_client.post("/decision", json=body, headers=director_headers)

    assert response.status_code == 400
    assert response.json == {"message": "Field voters is missing."}


def test_a_bad_address_anywhere_in_the_list_is_rejected(
    director_client, director_headers, waiting_order, voters
):
    response = decide(
        director_client, director_headers, uuid=waiting_order, voters=[*voters, "not-an-address"]
    )

    assert response.status_code == 400
    assert response.json == {"message": "Invalid voter address."}


def test_the_bad_address_is_reported_before_the_even_count(
    director_client, director_headers, waiting_order, voters
):
    # Four entries, so both rules are broken at once.
    response = decide(
        director_client, director_headers, uuid=waiting_order, voters=[*voters, "nope"]
    )

    assert response.json == {"message": "Invalid voter address."}


def test_an_even_number_of_voters_is_rejected(
    director_client, director_headers, waiting_order, voters, contracts
):
    response = decide(director_client, director_headers, uuid=waiting_order, voters=voters[:2])

    assert response.status_code == 400
    assert response.json == {"message": "Even number of voters."}
    assert live_contracts(contracts) == {}


def test_a_rejected_decision_leaves_the_order_pending(
    director_client, director_headers, waiting_order, orders
):
    decide(director_client, director_headers, uuid=waiting_order, voters=["nope"])

    assert pending(orders) == {waiting_order}


def test_decision_needs_a_director_token(director_client, employee_headers):
    response = decide(director_client, employee_headers, uuid=str(uuid.uuid4()), voters=["0x0"])

    assert response.status_code == 401

    assert director_client.post("/decision", json={}).status_code == 401


# --- deployment -------------------------------------------------------------


def test_a_decision_deploys_a_contract_and_returns_both_transactions(
    director_client, director_headers, waiting_order, voters, contracts, ganache
):
    response = decide(director_client, director_headers, uuid=waiting_order, voters=voters)

    assert response.status_code == 200

    registry = live_contracts(contracts)

    assert list(registry) == [waiting_order]

    address = registry[waiting_order]

    assert ganache.eth.get_code(address) != b""

    for name in ["approve_transaction", "reject_transaction"]:
        transaction = response.json[name]

        assert transaction["to"] == address
        assert transaction["gas"] > 0
        # The sender is whichever voter ends up casting it, so it cannot be
        # baked in here.
        assert "from" not in transaction
        assert "nonce" not in transaction

    assert (
        response.json["approve_transaction"]["data"] != response.json["reject_transaction"]["data"]
    )


def test_the_order_stays_pending_until_the_vote_concludes(
    director_client, director_headers, waiting_order, voters, orders
):
    decide(director_client, director_headers, uuid=waiting_order, voters=voters)

    assert pending(orders) == {waiting_order}


def test_the_returned_transactions_are_castable(
    director_service, director_client, director_headers, waiting_order, voters, ganache
):
    approve = decide(director_client, director_headers, uuid=waiting_order, voters=voters).json[
        "approve_transaction"
    ]

    ganache.eth.wait_for_transaction_receipt(
        ganache.eth.send_transaction({**approve, "from": voters[0]})
    )

    ended, _ = director_service.utilities.voting_status(approve["to"])

    # One approval out of three voters is not yet a majority.
    assert not ended


# --- the poller closes the loop --------------------------------------------


def cast(ganache, transaction, sender):
    ganache.eth.wait_for_transaction_receipt(
        ganache.eth.send_transaction({**transaction, "from": sender})
    )


def test_nothing_happens_while_the_vote_is_open(
    director_service,
    director_client,
    director_headers,
    waiting_order,
    voters,
    orders,
    contracts,
    assets,
):
    decide(director_client, director_headers, uuid=waiting_order, voters=voters)

    assert director_service.apply_concluded_votes() == []
    assert pending(orders) == {waiting_order}
    assert len(live_contracts(contracts)) == 1
    assert assets.count_documents({}) == 0


def test_a_majority_of_approvals_writes_the_asset(
    director_service,
    director_client,
    director_headers,
    waiting_order,
    voters,
    orders,
    contracts,
    assets,
    ganache,
):
    approve = decide(director_client, director_headers, uuid=waiting_order, voters=voters).json[
        "approve_transaction"
    ]

    before = datetime.now(UTC)

    cast(ganache, approve, voters[0])
    cast(ganache, approve, voters[1])

    assert director_service.apply_concluded_votes() == [waiting_order]

    asset = assets.find_one({"name": "Ferrari F40"})

    assert asset["categories"] == ["vehicles", "luxury"]
    assert asset["buying_price"] == 500000
    assert asset["info"] == {"engine": {"power": 350}}
    assert asset["buying_date"].replace(tzinfo=UTC) >= before

    # Both the order and the contract are retired.
    assert pending(orders) == set()
    assert live_contracts(contracts) == {}


def test_a_majority_of_rejections_writes_nothing(
    director_service,
    director_client,
    director_headers,
    waiting_order,
    voters,
    orders,
    contracts,
    assets,
    ganache,
):
    reject = decide(director_client, director_headers, uuid=waiting_order, voters=voters).json[
        "reject_transaction"
    ]

    cast(ganache, reject, voters[0])
    cast(ganache, reject, voters[2])

    assert director_service.apply_concluded_votes() == [waiting_order]

    assert assets.count_documents({}) == 0
    assert pending(orders) == set()
    assert live_contracts(contracts) == {}


def test_an_approved_sale_updates_the_existing_asset(
    director_service,
    employee_client,
    employee_headers,
    director_client,
    director_headers,
    voters,
    orders,
    assets,
    ganache,
):
    identifier = assets.insert_one(
        {
            "name": "Villa",
            "categories": ["real estate"],
            "buying_price": 100000,
            "buying_date": datetime(2025, 1, 15, 9, 0, 0),
            "info": {},
        }
    ).inserted_id

    employee_client.post(
        "/create_sell_order",
        json={"id": str(identifier), "selling_price": 150000},
        headers=employee_headers,
    )

    order_uuid = only_uuid(orders)

    approve = decide(director_client, director_headers, uuid=order_uuid, voters=voters).json[
        "approve_transaction"
    ]

    cast(ganache, approve, voters[0])
    cast(ganache, approve, voters[2])

    assert director_service.apply_concluded_votes() == [order_uuid]

    asset = assets.find_one({"_id": identifier})

    assert asset["selling_price"] == 150000
    assert "selling_date" in asset
    assert assets.count_documents({}) == 1


def test_a_settled_vote_is_only_applied_once(
    director_service,
    director_client,
    director_headers,
    waiting_order,
    voters,
    assets,
    ganache,
):
    approve = decide(director_client, director_headers, uuid=waiting_order, voters=voters).json[
        "approve_transaction"
    ]

    cast(ganache, approve, voters[0])
    cast(ganache, approve, voters[1])

    director_service.apply_concluded_votes()
    # A second pass must not insert the asset again.
    assert director_service.apply_concluded_votes() == []
    assert assets.count_documents({}) == 1


def test_two_votes_settle_independently(
    director_service,
    employee_client,
    employee_headers,
    director_client,
    director_headers,
    voters,
    orders,
    contracts,
    assets,
    ganache,
):
    propose_buy(employee_client, employee_headers)
    propose_buy(employee_client, employee_headers, name="Zastava 101")

    first, second = sorted(pending(orders))

    approve_first = decide(director_client, director_headers, uuid=first, voters=voters).json[
        "approve_transaction"
    ]
    decide(director_client, director_headers, uuid=second, voters=voters)

    cast(ganache, approve_first, voters[0])
    cast(ganache, approve_first, voters[1])

    assert director_service.apply_concluded_votes() == [first]

    # The second vote is still open, so its order and contract stay put.
    assert pending(orders) == {second}
    assert list(live_contracts(contracts)) == [second]
    assert assets.count_documents({}) == 1


def test_the_stored_order_shape_survives_the_round_trip(
    director_service, director_client, director_headers, waiting_order, voters, orders, ganache
):
    stored = json.loads(orders.hget(Configuration.REDIS_ORDERS, waiting_order))

    assert stored["order_type"] == "BUY"

    approve = decide(director_client, director_headers, uuid=waiting_order, voters=voters).json[
        "approve_transaction"
    ]

    cast(ganache, approve, voters[0])
    cast(ganache, approve, voters[1])

    assert director_service.apply_concluded_votes() == [waiting_order]
