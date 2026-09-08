import os

DATABASE_URL = os.environ["DATABASE_URL"]


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql://root:root@{DATABASE_URL}/employees"
