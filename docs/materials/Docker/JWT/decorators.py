def dashes_decorator(function_to_decorate):
    def wrapper():
        result = function_to_decorate()
        return "----" + str(result) + "-----"

    return wrapper


def stars_decorator(function_to_decorate):
    def wrapper():
        result = function_to_decorate()
        return "****" + str(result) + "****"

    return wrapper


def decorator_with_an_argument(argument):
    def decorator(function_to_decorate):
        def wrapper():
            result = function_to_decorate()
            return str(argument) + str(result) + str(argument)

        return wrapper

    return decorator


@decorator_with_an_argument("IEP")
@dashes_decorator
@stars_decorator
def foo():
    return "foo"


def general_purpose_decorator(argument):
    def decorator(function_to_decorate):
        def wrapper(*function_args, **function_kwargs):
            result = function_to_decorate(*function_args, **function_kwargs)
            return str(argument) + str(result) + str(argument)

        return wrapper

    return decorator


@general_purpose_decorator("<BAR>")
def bar(*args, **kwargs):
    return f"ARGS = {args}, KWARGS = {kwargs}"


from functools import wraps

from flask_jwt_extended import get_jwt, jwt_required


def role_check(role):
    def decorator(function):
        @jwt_required()
        @wraps(function)
        def wrapper(*args, **kwargs):
            # verify_jwt_in_request ( )
            claims = get_jwt()
            if role in claims["roles"]:
                return function(*args, **kwargs)
            else:
                return "Invalid role", 401

        return wrapper

    return decorator


if __name__ == "__main__":
    print(foo())
    print(bar(1, 2, 3, key0="value0", key1="value1"))
