"""Call one route of the running system, with a token, and print what came back.

Runs inside one of the project's own images, so the defense machine needs
nothing but Docker. See deploy/proveri.sh and deploy/proveri.cmd.

    proveri.sh director /report
    proveri.sh employee /search post '{"name": "Ferrari"}'
    proveri.sh director "/report?from=2020-01-01&to=2030-01-01"
"""

import json
import os
import sys

import requests

AUTHENTICATION = os.environ.get("AUTHENTICATION_URL", "http://host.docker.internal:5000")
EMPLOYEE = os.environ.get("EMPLOYEE_URL", "http://host.docker.internal:5001")
DIRECTOR = os.environ.get("DIRECTOR_URL", "http://host.docker.internal:5002")

DIRECTOR_ACCOUNT = {"email": "onlymoney@gmail.com", "password": "evenmoremoney"}
EMPLOYEE_ACCOUNT = {
    "forename": "Provera",
    "surname": "Provera",
    "email": "provera@gmail.com",
    "password": "provera123",
}


def token(account):
    """A token for `account`, registering the employee first if it is new."""

    response = requests.post(AUTHENTICATION + "/login", json=account, timeout=15)

    if response.status_code != 200:
        requests.post(AUTHENTICATION + "/register", json=EMPLOYEE_ACCOUNT, timeout=15)
        response = requests.post(AUTHENTICATION + "/login", json=account, timeout=15)

    response.raise_for_status()

    return response.json()["accessToken"]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    service, route = sys.argv[1], sys.argv[2]
    method = "get"
    body = None

    for argument in sys.argv[3:]:
        if argument.lower() in ("get", "post", "put", "delete"):
            method = argument.lower()
        else:
            method, body = "post", json.loads(argument)

    if service == "director":
        url, account = DIRECTOR, DIRECTOR_ACCOUNT
    elif service == "employee":
        url, account = EMPLOYEE, {k: EMPLOYEE_ACCOUNT[k] for k in ("email", "password")}
    else:
        url, account = AUTHENTICATION, DIRECTOR_ACCOUNT

    headers = {"Authorization": f"Bearer {token(account)}"}

    response = requests.request(method, url + route, headers=headers, json=body, timeout=30)

    print(f"{method.upper()} {url + route} -> {response.status_code}")

    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except ValueError:
        print(response.text)

    return 0 if response.status_code < 400 else 1


if __name__ == "__main__":
    sys.exit(main())
