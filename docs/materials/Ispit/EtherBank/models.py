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
    email = database.Column(database.String(256), nullable=False, unique=True)
    password = database.Column(database.String(256), nullable=False)
    account_address = database.Column(database.String(64), nullable=False)

    roles = database.relationship("Role", secondary=UserRole.__table__, back_populates="users")

    def __init__(self, email, password, account_address):
        self.email = email
        self.password = password
        self.account_address = account_address


class Role(database.Model):
    __tablename__ = "roles"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)

    users = database.relationship("User", secondary=UserRole.__table__, back_populates="roles")

    def __init__(self, name):
        self.name = name


class Account(database.Model):
    __tablename__ = "accounts"

    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey("users.id"), nullable=False)
    contract_address = database.Column(database.String(64), nullable=False)

    def __init__(self, user_id, contract_address):
        self.user_id = user_id
        self.contract_address = contract_address
