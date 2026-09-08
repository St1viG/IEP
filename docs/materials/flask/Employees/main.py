from logging.config import dictConfig

from flask import Flask, jsonify, request

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["wsgi"],
        },
    }
)

application = Flask(__name__)


@application.route("/", methods=["GET"])
def hello_world():
    application.logger.info("GET /")
    return "<h1>Hello world!</h1>"


class Employee:
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


employees = []


def serialize_employees(items):
    return [str(employee) for employee in items]


@application.route("/add", methods=["POST"])
def add():
    payload = request.get_json(silent=True)
    if payload is None:
        application.logger.warning("POST /add invalid or missing JSON body")
        return jsonify(error="Request body must be valid JSON."), 400

    new_employee = Employee(**payload)

    employees.append(new_employee)
    application.logger.info("Employee added email=%s total=%d", new_employee.email, len(employees))

    return jsonify(employees=serialize_employees(employees))


@application.route("/upload", methods=["POST"])
def upload():
    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        application.logger.warning("POST /upload missing file in request")
        return jsonify(error="Missing file"), 400

    application.logger.info("POST /upload filename=%s", uploaded_file.filename or "<unnamed>")

    try:
        content = uploaded_file.stream.read().decode()
    except UnicodeDecodeError:
        application.logger.exception(
            "POST /upload failed to decode filename=%s",
            uploaded_file.filename or "<unnamed>",
        )
        return jsonify(error="Unable to decode uploaded file"), 400

    added = 0
    for line_number, line in enumerate(content.splitlines(), start=1):
        if not line.strip():
            continue

        values = [value.strip() for value in line.split(",")]
        if len(values) != 6:
            application.logger.warning(
                "Skipping malformed CSV row line=%d value=%r", line_number, line
            )
            continue

        employees.append(Employee(*values))
        added += 1

    application.logger.info(
        "Upload complete filename=%s added=%d total=%d",
        uploaded_file.filename or "<unnamed>",
        added,
        len(employees),
    )

    return jsonify(employees=serialize_employees(employees))


@application.route("/search", methods=["GET"])
def search():
    result = employees
    criteria = ["first_name", "last_name", "email", "gender", "language", "position"]
    filters = {}

    for criterium in criteria:
        if criterium in request.args:
            filters[criterium] = request.args[criterium]
            result = [
                employee
                for employee in result
                if request.args[criterium] in getattr(employee, criterium)
            ]

    application.logger.info("GET /search filters=%s matches=%d", filters, len(result))
    return jsonify(employees=serialize_employees(result))


if __name__ == "__main__":
    application.logger.info("Starting development server")
    application.run(debug=True)
