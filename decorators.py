from functools import wraps

from flask_jwt_extended import get_jwt
from flask_jwt_extended import jwt_required


def role_check ( role ):
    def decorator ( function ):
        @jwt_required ( )
        @wraps ( function )
        def wrapper ( *args, **kwargs ):
            claims = get_jwt ( )

            if ( role in claims["roles"] ):
                return function ( *args, **kwargs )
            else:
                return "Invalid role", 401

        return wrapper

    return decorator
