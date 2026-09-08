from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class User(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String(256), nullable=False)
    password = database.Column(database.String(256), nullable=False)
