from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from pydantic import BaseModel, ConfigDict, EmailStr, ValidationError

application = Flask(__name__)


@application.route("/", methods=["GET"])
def hello_world():
    return "<h1>Hello world!</h1>"


# Create and configure a SQLAlchemy object
application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
database = SQLAlchemy()
database.init_app(application)


class Employee(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    first_name = database.Column(database.String(64), nullable=False)
    last_name = database.Column(database.String(64), nullable=False)
    email = database.Column(database.String(64), nullable=False, unique=True)
    gender = database.Column(database.String(64), nullable=False)
    language = database.Column(database.String(64), nullable=False)
    position = database.Column(database.String(64), nullable=False)

    # added for migrate demo, has to be nullable
    # dummy = database.Column(database.Integer)

    def __init__(self, first_name, last_name, email, gender, language, position):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.gender = gender
        self.language = language
        self.position = position

    def __repr__(self):
        return (
            f"<Employee {self.first_name}, {self.last_name}, {self.email}, "
            f"{self.gender}, {self.language}, {self.position}>"
        )


class EmployeeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    first_name: str
    last_name: str
    email: EmailStr
    gender: str
    language: str
    position: str


# These lines can be used to create the database
with application.app_context():
    database.create_all()

# This line is used to alter the table after the dummy column is added
# migrate = Migrate(application, database)


@application.route("/add", methods=["POST"])
def add():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify(error="Request body must be valid JSON."), 400

    try:
        employee_data = EmployeeCreate.model_validate(payload)
    except ValidationError as error:
        return jsonify(errors=error.errors()), 400

    new_employee = Employee(**employee_data.model_dump())

    database.session.add(new_employee)
    database.session.commit()

    # select * from employee;
    employees = Employee.query.all()
    return jsonify(employees=[str(employee) for employee in employees])


@application.route("/upload", methods=["POST"])
def upload():
    content = request.files["file"].stream.read().decode()

    for line in content.split("\n"):
        new_employee = Employee(*line.split(","))
        database.session.add(new_employee)

    database.session.commit()
    employees = Employee.query.all()

    return jsonify(employees=[str(employee) for employee in employees])


@application.route("/search", methods=["GET"])
def search():
    criteria = ["first_name", "last_name", "email", "gender", "language", "position"]

    filters = []
    for criterium in criteria:
        if criterium in request.args:
            filters.append(getattr(Employee, criterium).like(f"%{request.args[criterium]}%"))

    query = Employee.query.filter(*filters)
    print(query)
    result = query.all()
    return jsonify(employees=[str(employee) for employee in result])


if __name__ == "__main__":
    application.run(debug=True)
