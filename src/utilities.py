"""The blockchain half of the director service.

The contract is compiled ahead of time and its artifacts are committed, the way
every course example ships them, so nothing here invokes solc. Ganache's first
account is unlocked, which is what pays for each deployment and why no private
key is ever handled.
"""

import json
from pathlib import Path

from eth_utils import is_checksum_formatted_address
from web3 import HTTPProvider, Web3

from configuration import Configuration

# src/utilities.py -> repo root -> contracts/output. Inside an image the module
# sits at /utilities.py, so the same expression resolves to /contracts/output,
# which is where the dockerfile puts the artifacts.
CONTRACT_DIRECTORY = Path(__file__).resolve().parent.parent / "contracts" / "output"

# vote_approve and vote_reject cost well under 100k. The transactions are handed
# out before a sender is known, so the limit is fixed rather than estimated.
VOTE_GAS = 200000


def get_web3():
    return Web3(HTTPProvider(Configuration.BLOCKCHAIN_URL, request_kwargs={"timeout": 30}))


def read_contract(name="Voting"):
    """The abi as a parsed list and the bytecode as a hex string."""

    abi = json.loads((CONTRACT_DIRECTORY / f"{name}.abi").read_text())
    # A stray newline here would be read into the deploy transaction as bytecode.
    bytecode = (CONTRACT_DIRECTORY / f"{name}.bin").read_text().strip()

    return abi, bytecode


def deploy_voting(voters):
    """Deploy one Voting contract for the given voters and return its address.

    Paid for by the first account ganache creates at startup, which is unlocked,
    so there is no key to manage.
    """

    web3 = get_web3()
    abi, bytecode = read_contract()

    factory = web3.eth.contract(abi=abi, bytecode=bytecode)

    # Checksummed on the way in: web3 encodes an address argument only in its
    # canonical form, and valid_address has already ruled out anything that
    # cannot be converted.
    addresses = [Web3.to_checksum_address(voter) for voter in voters]

    transaction = factory.constructor(addresses).transact({"from": web3.eth.accounts[0]})
    receipt = web3.eth.wait_for_transaction_receipt(transaction)

    return receipt["contractAddress"]


def vote_transactions(address):
    """The two unsigned transactions a voter can send, one per outcome.

    Neither carries `from` or `nonce`: any of the allowed voters may cast either
    one, and which of them does is not known when the contract is deployed. The
    voter fills those in before signing.
    """

    web3 = get_web3()
    abi, _ = read_contract()

    contract = web3.eth.contract(address=address, abi=abi)

    def transaction(function):
        return {
            "to": address,
            "data": contract.encode_abi(function),
            "gas": VOTE_GAS,
            "gasPrice": web3.eth.gas_price,
            "chainId": web3.eth.chain_id,
        }

    return transaction("vote_approve"), transaction("vote_reject")


def voting_status(address):
    """(ended, approved) as the contract currently sees it."""

    web3 = get_web3()
    abi, _ = read_contract()

    ended, approved = web3.eth.contract(address=address, abi=abi).functions.status().call()

    return ended, approved


def valid_address(value):
    if not isinstance(value, str) or not Web3.is_address(value):
        return False

    # is_address lets a mixed case address through whatever its EIP-55 checksum
    # says, but web3 refuses that same address again from deep inside the deploy
    # and the failure would surface as a 500. Reject it here, where the spec
    # still has "Invalid voter address." to answer with.
    return not is_checksum_formatted_address(value) or Web3.is_checksum_address(value)
