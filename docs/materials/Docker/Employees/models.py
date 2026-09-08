from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class Employee(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    first_name = database.Column(database.String(256), nullable=False)
    last_name = database.Column(database.String(256), nullable=False)
    email = database.Column(database.String(256), nullable=False)
    gender = database.Column(database.String(256), nullable=False)
    language = database.Column(database.String(256), nullable=False)
    position = database.Column(database.String(256), nullable=False)

    tasks = database.relationship("Task", back_populates="employee")

    def __init__(self, first_name, last_name, email, gender, language, position):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.gender = gender
        self.language = language
        self.position = position

    def __repr__(self):
        return f"<Employee {self.first_name}, {self.last_name}, {self.email}, {self.gender}, {self.language}, {self.position}>"


class Task(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    description = database.Column(database.String(256), nullable=False)
    employee_id = database.Column(
        database.Integer, database.ForeignKey(Employee.id), nullable=False
    )

    employee = database.relationship("Employee", back_populates="tasks")
