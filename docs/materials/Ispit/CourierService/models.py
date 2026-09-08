from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class Delivery(database.Model):
    __tablename__ = "deliveries"

    id = database.Column(database.Integer, primary_key=True)
    contract_address = database.Column(database.String(64), nullable=True)

    package_id = database.Column(
        database.Integer, database.ForeignKey("packages.id"), nullable=False
    )
    courier_id = database.Column(
        database.Integer, database.ForeignKey("couriers.id"), nullable=False
    )

    courier = database.relationship("Courier", back_populates="deliveries")
    package = database.relationship("Package", back_populates="delivery")

    def __init__(self, contract_address, package_id, courier_id):
        self.contract_address = contract_address
        self.package_id = package_id
        self.courier_id = courier_id

    def __repr__(self):
        return f"<Delivery id={self.id}, status={self.status}, contract_address={self.contract_address}, package_id={self.package_id}, courier_id={self.courier_id}>"


class Courier(database.Model):
    __tablename__ = "couriers"

    id = database.Column(database.Integer, primary_key=True)
    email = database.Column(database.String(256), nullable=False, unique=True)
    forename = database.Column(database.String(256), nullable=False)
    surname = database.Column(database.String(256), nullable=False)

    deliveries = database.relationship("Delivery", back_populates="courier")

    def __init__(self, email, forename, surname):
        self.email = email
        self.forename = forename
        self.surname = surname

    def __repr__(self):
        return f"<Courier id={self.id}, email={self.email} forename={self.forename} surname={self.surname}>"


class Package(database.Model):
    __tablename__ = "packages"

    id = database.Column(database.Integer, primary_key=True)
    description = database.Column(database.String(256), nullable=False)
    delivery_price = database.Column(database.Integer, nullable=False)
    arrival_date = database.Column(database.DateTime, nullable=False)

    delivery = database.relationship("Delivery", back_populates="package")

    def __init__(self, description, delivery_price, arrival_date):
        self.description = description
        self.delivery_price = delivery_price
        self.arrival_date = arrival_date
