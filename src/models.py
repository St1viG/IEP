"""The relational half of the system: users, roles, and the join between them.

Only the authentication service and the migration job import this. Neither the
employee nor the director service speaks SQL at all.
"""

from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class UserRole(database.Model):
    __tablename__ = "user_role"

    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey("users.id"), nullable=False)
    role_id = database.Column(database.Integer, database.ForeignKey("roles.id"), nullable=False)

    def __init__(self, user_id, role_id):
        self.user_id = user_id
        self.role_id = role_id


class User(database.Model):
    __tablename__ = "users"

    id = database.Column(database.Integer, primary_key=True)
    forename = database.Column(database.String(256), nullable=False)
    surname = database.Column(database.String(256), nullable=False)
    email = database.Column(database.String(256), nullable=False, unique=True)
    password = database.Column(database.String(256), nullable=False)

    roles = database.relationship("Role", secondary=UserRole.__table__, back_populates="users")

    def __init__(self, forename, surname, email, password):
        self.forename = forename
        self.surname = surname
        self.email = email
        self.password = password


class Role(database.Model):
    __tablename__ = "roles"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)

    users = database.relationship("User", secondary=UserRole.__table__, back_populates="roles")

    def __init__(self, name):
        self.name = name
