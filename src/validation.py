"""The ordered checks every endpoint shares.

The order matters and is graded: each endpoint in the specification ends with
"Odgovarajuce provere se vrse u navedenom redosledu", so a request that breaks
two rules at once has to report the first one. Callers run these top to bottom
and return on the first failure.
"""

import re
import uuid

# The top level domain needs at least two characters: "john@gmail.a" is not
# an address, and neither is "john@gmail." or "john@gmail".
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s.]{2,}$")


def missing_field(body, names):
    for name in names:
        if name not in body:
            return name

        if isinstance(body[name], str) and len(body[name]) == 0:
            return name

    return None


def missing_field_message(name):
    return f"Field {name} is missing."


def valid_email(value):
    return isinstance(value, str) and EMAIL_PATTERN.match(value) is not None


def valid_price(value):
    # isinstance ( True, int ) is True, so booleans have to be excluded by hand.
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def valid_uuid(value):
    if not isinstance(value, str):
        return False

    try:
        uuid.UUID(value)
    except ValueError:
        return False

    return True
