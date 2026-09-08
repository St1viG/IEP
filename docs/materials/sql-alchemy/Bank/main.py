CONNECTION_STRING = "sqlite:///bank.sqlite3"

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, between, desc, distinct, func, not_, or_
from sqlalchemy.orm import aliased

application = Flask(__name__)
application.config["SQLALCHEMY_DATABASE_URI"] = CONNECTION_STRING

database = SQLAlchemy(application)


class City(database.Model):
    __tablename__ = "Mesto"

    id = database.Column("IdMes", database.Integer, primary_key=True)
    postal_code = database.Column("PostBr", database.String(6), unique=True)
    name = database.Column("Naziv", database.String(50))

    # City<->HasSeatIn one-to-many
    has_seat_in_list = database.relationship("HasSeatIn", back_populates="city")

    # City<->Branch one-to-many
    branches = database.relationship("Branch", back_populates="city")

    def __repr__(self):
        return f"City ( {self.id}, {self.postal_code}, {self.name} )"


class Client(database.Model):
    __tablename__ = "Komitent"

    id = database.Column("IdKom", database.Integer, primary_key=True)
    name = database.Column("Naziv", database.String(50))
    address = database.Column("Adresa", database.String(50))

    # Client<->HasSeatIn one-to-one
    has_seat_in = database.relationship("HasSeatIn", back_populates="client", uselist=False)

    # Client<->Account many-to-one
    accounts = database.relationship("Account", back_populates="client")

    def __repr__(self):
        return f"Client ( {self.id}, {self.name}, {self.address} )"


class HasSeatIn(database.Model):
    __tablename__ = "ImaSediste"

    client_id = database.Column("IdKom", database.ForeignKey(Client.id), primary_key=True)
    city_id = database.Column("IdMes", database.ForeignKey(City.id))

    # City<->HasSeatIn one-to-many
    city = database.relationship("City", back_populates="has_seat_in_list")

    # Client<->HasSeatIn one-to-one
    client = database.relationship("Client", back_populates="has_seat_in")

    def __repr__(self):
        return f"HasSeatIn ( {self.client_id}, {self.city_id} )"


class Branch(database.Model):
    __tablename__ = "Filijala"

    id = database.Column("IdFil", database.Integer, primary_key=True)
    name = database.Column("Naziv", database.String(50))
    address = database.Column("Adresa", database.String(50))
    city_id = database.Column("IDMes", database.ForeignKey(City.id))

    # City<->Branch one-to-many
    city = database.relationship("City", back_populates="branches")

    # Branch<->Account many-to-one
    accounts = database.relationship("Account", back_populates="branch")

    # Branch<->AccountItem many-to-one
    account_items = database.relationship("AccountItem", back_populates="branch")

    def __repr__(self):
        return f"Branch ( {self.id}, {self.name}, {self.address}, {self.city_id} )"


class Account(database.Model):
    __tablename__ = "Racun"

    id = database.Column("IdRac", database.Integer, primary_key=True)
    status = database.Column("Status", database.String(1))
    number_of_account_items = database.Column("BrojStavki", database.Integer)
    allowed_overdraft = database.Column("DozvMinus", database.Integer)
    balance = database.Column("Stanje", database.Integer)
    branch_id = database.Column("IdFil", database.ForeignKey(Branch.id))
    client_id = database.Column("IdKom", database.ForeignKey(Client.id))

    # Branch<->Account many-to-on
    branch = database.relationship("Branch", back_populates="accounts")

    # Client<->Account many-to-one
    client = database.relationship("Client", back_populates="accounts")

    # Account<->AccountItem many-to-one
    account_items = database.relationship("AccountItem", back_populates="account")

    def __repr__(self):
        return f"Account ( {self.id}, {self.status}, {self.number_of_account_items}, {self.allowed_overdraft}, {self.balance} )"


class AccountItem(database.Model):
    __tablename__ = "Stavka"

    id = database.Column("IdSta", database.Integer, primary_key=True)
    serial_number = database.Column("RedBroj", database.Integer)
    date = database.Column("Datum", database.Date)
    time = database.Column("Vreme", database.Time)
    amount = database.Column("Iznos", database.Integer)
    branch_id = database.Column("IdFil", database.ForeignKey(Branch.id))
    account_id = database.Column("IdRac", database.ForeignKey(Account.id))

    # Branch<->AccountItem many-to-one
    branch = database.relationship("Branch", back_populates="account_items")

    # Account<->AccountItem many-to-one
    account = database.relationship("Account", back_populates="account_items")

    # AccountItem<->Deposit one-to-one
    deposit = database.relationship("Deposit", back_populates="account_item", uselist=False)

    # AccountItem<->Withdrawal one-to-one
    withdrawal = database.relationship("Withdrawal", back_populates="account_item", uselist=False)

    def __repr__(self):
        return f"AccountItem ( {self.id}, {self.serial_number}, {self.date}, {self.time}, {self.time} )"


class Deposit(database.Model):
    __tablename__ = "Uplata"

    account_item_id = database.Column(
        "IdSta", database.ForeignKey(AccountItem.id), primary_key=True
    )
    basis = database.Column("Osnov", database.String(10))

    # AccountItem<->Deposit one-to-one
    account_item = database.relationship("AccountItem", back_populates="deposit")

    def __repr__(self):
        return f"Deposit ( {self.account_item}, {self.basis} )"


class Withdrawal(database.Model):
    __tablename__ = "Isplata"

    account_item_id = database.Column(
        "IdSta", database.ForeignKey(AccountItem.id), primary_key=True
    )
    commission = database.Column("Provizija", database.Float)

    # AccountItem<->Withdrawal one-to-one
    account_item = database.relationship("AccountItem", back_populates="withdrawal")

    def __repr__(self):
        return f"Withdrawal ( {self.account_item}, {self.commission} )"


def z01():
    return Client.query.all()


def z02():
    return Account.query.all()


def z03():
    return database.session.query(Client.name).all()


def z04():
    return database.session.query(Client.name, Client.address).all()


def z05():
    return Client.query.order_by(Client.name).all()


def z06():
    return Client.query.order_by(desc(Client.name)).all()


def z07():
    return Client.query.order_by(Client.name, Client.address).all()


def z08():
    return Client.query.order_by(Client.name, desc(Client.address)).all()


def z09():
    return Account.query.filter(Account.balance == -55000).all()


def z10():
    return Account.query.filter(Account.balance > 0).all()


def z11():
    return Account.query.filter(Account.status == "B").all()


def z12():
    return Account.query.filter(and_(Account.status == "B", Account.balance < -50000)).all()


def z13():
    return Account.query.filter(or_(Account.status == "B", Account.balance < -50000)).all()


def z14():
    return (
        database.session.query(Account.balance)
        .filter(and_(Account.status == "B", Account.balance < -50000))
        .all()
    )


def z15():
    return Account.query.filter(between(Account.balance, -12000, 10000)).all()


def z16():
    return (
        database.session.query(Account.balance, 3, Account.balance * -0.03)
        .filter(Account.balance < 0)
        .all()
    )


def z17():
    return (
        database.session.query(
            Account.id,
            Account.status,
            Account.number_of_account_items,
            Account.allowed_overdraft,
            Account.status,
            Account.balance * 1.03 < -Account.allowed_overdraft,
        )
        .filter(Account.balance < 0)
        .all()
    )


def z18():
    return (
        database.session.query(Account.balance, 3, Account.balance * -0.03)
        .filter(Account.balance < 0)
        .all()
    )


def z19():
    return (
        database.session.query(Account.id, Account.balance + Account.allowed_overdraft)
        .filter(Account.balance > -Account.allowed_overdraft)
        .all()
    )


def z20():
    return database.session.query(distinct(Client.name)).all()


def z21():
    return Account.query.filter(Account.balance == None).all()


def z22():
    return Account.query.filter(Account.balance != None).all()


def z23():
    return database.session.query(func.sum(Account.balance)).all()


def z24():
    return database.session.query(func.min(Account.balance)).filter(Account.balance > 0).all()


def z25():
    return database.session.query(
        func.avg(Account.balance),
        func.sum(Account.balance) / func.count(Account.balance),
        func.sum(Account.balance) / func.count("*"),
    ).all()


def z26():
    return (
        database.session.query(Client.name, Account.balance)
        .filter(Client.id == Account.client_id)
        .all()
    )


def z27():
    return (
        database.session.query(Branch.name, AccountItem.amount, AccountItem.account_id)
        .filter(Branch.id == AccountItem.branch_id)
        .all()
    )


def z28():
    branchAccountItem = aliased(Branch)
    branchAccount = aliased(Branch)
    return (
        database.session.query(
            branchAccountItem.name, AccountItem.amount, Account.id, branchAccount.name
        )
        .filter(
            and_(
                branchAccountItem.id == AccountItem.branch_id,
                AccountItem.account_id == Account.id,
                branchAccount.id == Account.branch_id,
            )
        )
        .all()
    )


def z29():
    return (
        database.session.query(Branch.name, AccountItem.amount)
        .join(Branch.account_items)
        .join(AccountItem.deposit)
        .filter(Deposit.basis == "Plata")
        .all()
    )


def z30():
    return (
        database.session.query(Account.client_id, func.sum(Account.balance))
        .group_by(Account.client_id)
        .all()
    )


def z31():
    return (
        database.session.query(
            AccountItem.account_id, func.count("*"), func.sum(AccountItem.amount)
        )
        .join(AccountItem.deposit)
        .group_by(AccountItem.account_id)
        .all()
    )


def z32():
    return (
        database.session.query(Client.name, func.sum(Account.balance))
        .join(Client.accounts)
        .group_by(Client.id, Client.name)
        .all()
    )


def z33():
    return (
        database.session.query(Client.name, func.count("*"))
        .join(Client.accounts)
        .filter(Account.status == "A")
        .group_by(Client.id, Client.name)
        .all()
    )


def z34():
    return (
        database.session.query(Client.name, func.count("*"))
        .join(Client.accounts)
        .filter(Account.balance > 0)
        .group_by(Client.id, Client.name)
        .all()
    )


def z35():
    return (
        database.session.query(Client.name, func.sum(Account.balance))
        .join(Client.accounts)
        .group_by(Client.id, Client.name)
        .having(func.sum(Account.balance) > 0)
        .all()
    )


def z36():
    return (
        database.session.query(Client.name)
        .join(Client.accounts)
        .group_by(Client.id, Client.name)
        .having(func.count("*") == 2)
        .all()
    )


def z37():
    return (
        database.session.query(Client.name)
        .join(Client.accounts)
        .filter(Account.status == "A")
        .group_by(Client.id, Client.name)
        .having(func.count("*") == 2)
        .all()
    )


def z38():
    return (
        database.session.query(AccountItem.account_id)
        .group_by(AccountItem.account_id)
        .having(func.count(distinct(AccountItem.branch_id)) >= 2)
        .all()
    )


def z39():
    return (
        database.session.query(AccountItem.account_id)
        .join(AccountItem.branch)
        .group_by(AccountItem.account_id)
        .having(func.count(distinct(Branch.city_id)) >= 2)
        .all()
    )


def z40():
    return Branch.query.filter(not_(Branch.address.like("%trg%"))).all()


options = [
    z01,
    z02,
    z03,
    z04,
    z05,
    z06,
    z07,
    z08,
    z09,
    z10,
    z11,
    z12,
    z13,
    z14,
    z15,
    z16,
    z17,
    z18,
    z19,
    z20,
    z21,
    z22,
    z23,
    z24,
    z25,
    z26,
    z27,
    z28,
    z29,
    z30,
    z31,
    z32,
    z33,
    z34,
    z35,
    z36,
    z37,
    z38,
    z39,
    z40,
]

choices = [int(item) for item in input().split()]

with application.app_context():
    for choice in choices:
        print(f"RESULT {choice}:")
        print(options[choice - 1]())
