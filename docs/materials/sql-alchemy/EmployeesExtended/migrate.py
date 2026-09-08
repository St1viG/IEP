from flask import Flask
from flask_migrate import Migrate

from configuration import Configuration
from models import database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)

with application.app_context():
    database.create_all()

migrate = Migrate(application, database)
