from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class is_engaged(database.Model):
    __tablename__ = "is_engaged"

    employee_id = database.Column(
        database.Integer, database.ForeignKey("employees.id"), primary_key=True, nullable=False
    )
    task_id = database.Column(
        database.Integer, database.ForeignKey("tasks.id"), primary_key=True, nullable=False
    )


class Employee(database.Model):
    __tablename__ = "employees"

    id = database.Column(database.Integer, primary_key=True)
    forename = database.Column(database.String(64), nullable=False)
    surname = database.Column(database.String(64), nullable=False)
    email = database.Column(database.String(64), nullable=False)
    gender = database.Column(database.Integer, nullable=False)
    position = database.Column(database.String(64), nullable=False)

    dummy = database.Column(database.Integer)

    tasks = database.relationship(
        "Task", secondary=is_engaged.__table__, back_populates="employees"
    )

    bonuses = database.relationship("Bonus", backref="employee", lazy=True)

    def __init__(self, forename, surname, email, gender, position):
        self.forename = forename
        self.surname = surname
        self.email = email
        self.gender = gender
        self.position = position

    def __repr__(self):
        return f"<Employee({self.id}) {self.forename}, {self.surname}, {self.email}, {self.gender}, {self.position}>"


class Task(database.Model):
    __tablename__ = "tasks"

    id = database.Column(database.Integer, primary_key=True)
    description = database.Column(database.String(256), nullable=False)

    employees = database.relationship(
        "Employee", secondary=is_engaged.__table__, back_populates="tasks"
    )

    def __repr__(self):
        return f"<Task({self.id}) {self.description}>"


class Bonus(database.Model):
    __tablename__ = "bonuses"

    id = database.Column(database.Integer, primary_key=True)
    amount = database.Column(database.Float, nullable=False)
    reason = database.Column(database.String(256), nullable=False)
    employee_id = database.Column(
        database.Integer, database.ForeignKey("employees.id"), nullable=False
    )

    def __repr__(self):
        return f"<Bonus({self.id}) {self.amount} {self.reason} {self.employee_id}>"
