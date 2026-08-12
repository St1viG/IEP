import re
import uuid

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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
