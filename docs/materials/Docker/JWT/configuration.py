import os
from datetime import timedelta

DATABASE_URL_KEY = "DATABASE_URL"
DATABASE_USERNAME_KEY = "DATABASE_USERNAME"
DATABASE_PASSWORD_KEY = "DATABASE_PASSWORD"
DATABASE_NAME_KEY = "DATABASE_NAME"

DATABASE_URL = "localhost" if (DATABASE_URL_KEY not in os.environ) else os.environ[DATABASE_URL_KEY]
DATABASE_USERNAME = (
    "root" if (DATABASE_USERNAME_KEY not in os.environ) else os.environ[DATABASE_USERNAME_KEY]
)
DATABASE_PASSWORD = (
    "root" if (DATABASE_PASSWORD_KEY not in os.environ) else os.environ[DATABASE_PASSWORD_KEY]
)
DATABASE_NAME = "users" if (DATABASE_NAME_KEY not in os.environ) else os.environ[DATABASE_NAME_KEY]


class Configuration:
    # SQLALCHEMY_DATABASE_URI   = "sqlite:///database.db"
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}/{DATABASE_NAME}"
    )
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
