from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, jwt_required


def role_check(role):
    def decorator(function):
        @jwt_required()
        @wraps(function)
        def wrapper(*args, **kwargs):
            claims = get_jwt()

            if role in claims.get("roles", []):
                return function(*args, **kwargs)
            else:
                # The spec describes only the missing-header case, and a token
                # for the wrong role is no more an authorization for this route
                # than no token at all, so it gets the same answer.
                return jsonify(msg="Missing Authorization Header"), 401

        return wrapper

    return decorator
