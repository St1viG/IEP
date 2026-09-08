import os

DATABASE_URL = "database" if ("PRODUCTION" in os.environ) else "localhost"


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql://root:root@{DATABASE_URL}/employees"
