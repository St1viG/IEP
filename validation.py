import re

EMAIL_PATTERN = re.compile ( r"^[^@\s]+@[^@\s]+\.[^@\s]+$" )


def missing_field ( body, names ):
    for name in names:
        if name not in body:
            return name

        if isinstance ( body[name], str ) and len ( body[name] ) == 0:
            return name

    return None


def missing_field_message ( name ):
    return f"Field {name} is missing."


def valid_email ( value ):
    return isinstance ( value, str ) and EMAIL_PATTERN.match ( value ) is not None
