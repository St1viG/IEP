from flask import Flask, jsonify, request
from sqlalchemy import func, or_

from configuration import Configuration
from models import Bonus, Employee, Task, database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)


@application.route("/", methods=["GET"])
def hello_world():
    return "Hello world!"


# select * from employees
@application.route("/employees", methods=["GET"])
def employees():
    return [str(employee) for employee in Employee.query.all()]


# select * from employees where gender = 0
@application.route("/male_employees", methods=["GET"])
def male_employees():
    result = Employee.query.filter(Employee.gender == 0).all()
    return [str(employee) for employee in result]


# select * from employees where gender = 1
@application.route("/female_employees", methods=["GET"])
def female_employees():
    result = Employee.query.filter(Employee.gender == 1).all()
    return [str(employee) for employee in result]


# select * from tasks where description like '%keyword%'
@application.route("/tasks/<keyword>", methods=["GET"])
def tasks(keyword):
    result = Task.query.filter(Task.description.like(f"%{keyword}%")).all()
    return [str(task) for task in result]


# select *
# from bonuses
# where ( reason = '...' or reason = '...' or ... ) and amount >= ....
# amount is optional
@application.route("/bonuses", methods=["GET"])
def bonuses():
    query = Bonus.query

    reasons = request.args.getlist("reasons")

    query = query.filter(or_(*[Bonus.reason == reason for reason in reasons]))

    if "amount" in request.args:
        amount = float(request.args["amount"])
        query = query.filter(Bonus.amount >= amount)

    # printing a query before execution is a useful debugging tool
    print(query)
    result = query.all()
    return [str(bonus) for bonus in result]


# select employees.id, count ( "*" )
# from employees join is_engaged on ( employees.id = is_engaged.employee_id ) join tasks on ( is_engaged.task_id = tasks.id )
# group by employees.id
# having count ( "*" ) > min
# min is optional
@application.route("/tasks_per_employee", methods=["GET"])
def tasks_per_employee():
    query = (
        Employee.query.with_entities(Employee.id, func.count("*"))
        .join(Employee.tasks)
        .group_by(Employee.id)
    )

    if "min" in request.args:
        min = int(request.args["min"])
        query = query.having(func.count("*") >= min)

    print(query)
    result = query.all()
    return [str(item) for item in result]


# select employees.forename + " " + employess.surname, sum ( bonuses.amount )
# from employees join bonuses on ( employees.id = bonuses.employee_id )
# group by employees.id
@application.route("/total_bonus_per_employee", methods=["GET"])
def total_bonus_per_employee():
    query = (
        database.session.query(Employee.forename + " " + Employee.surname, func.sum(Bonus.amount))
        .join(Employee.bonuses)
        .group_by(Employee.id)
    )

    print(query)
    result = query.all()
    return [str(item) for item in result]


@application.route("/add_employees", methods=["POST"])
def add_employees():
    content = request.files["file"].stream.read().decode()

    for line in content.split("\n"):
        new_employee = Employee(*line.split(","))
        database.session.add(new_employee)

    database.session.commit()

    return jsonify(employees=[str(employee) for employee in Employee.query.all()])


@application.route("/search", methods=["GET"])
def search():
    criteria = ["forename", "surname", "email", "gender", "position"]

    filters = []
    for criterium in criteria:
        if criterium in request.args:
            if criterium == "gender":
                filters.append(Employee.gender == int(request.args["gender"]))
            else:
                filters.append(getattr(Employee, criterium).like(f"%{request.args[criterium]}%"))

    query = Employee.query.filter(*filters)
    print(query)
    result = query.all()
    return jsonify(employees=[str(employee) for employee in result])


if __name__ == "__main__":
    application.run(debug=True)
